from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal, Optional
import asyncio
import io
import json

import speech_recognition as sr
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from config.database import connect_to_mongo, close_mongo_connection
from services.seed_data import initialize_database
from agent.graph import agent


app = FastAPI()

# Configure CORS to allow all origins (useful for local development / testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


def build_langchain_messages(message: str, history: List[ChatMessage]):
    messages: List[HumanMessage | AIMessage] = []
    for item in history:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
    messages.append(HumanMessage(content=message))
    return messages



@app.on_event("startup")
async def startup_event() -> None:
    await connect_to_mongo()
    await initialize_database()

    async def _warmup_agent():
        dummy_messages = [HumanMessage(content="Hello, this is a warmup request. Respond briefly.")]
        try:
            await agent.ainvoke({"messages": dummy_messages})
        except Exception:
            return

    asyncio.create_task(_warmup_agent())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_mongo_connection()

@app.get("/")
def root_fun():
    return {
        "message":"all things are running"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    messages = build_langchain_messages(request.message, request.history)
    inputs = {"messages": messages}
    try:
        # Add timeout to prevent hanging (90 seconds should be enough for tool calls + response)
        result = await asyncio.wait_for(agent.ainvoke(inputs), timeout=90.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out. The agent took too long to respond.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc
    
    try:
        # Find the last AIMessage in the result (not just the last message, which might be a ToolMessage)
        ai_message = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, "content") and msg.content:
                # Check if content is a string and not empty
                content = msg.content
                if isinstance(content, str) and content.strip():
                    ai_message = content
                    break
                elif isinstance(content, list):
                    # Handle case where content might be a list of content blocks
                    text_parts = []
                    for part in content:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        ai_message = " ".join(text_parts)
                        break
        
        if ai_message is None or not ai_message.strip():
            # Fallback: try to get content from last message anyway
            last_msg = result["messages"][-1]
            if hasattr(last_msg, "content"):
                content = last_msg.content
                if isinstance(content, str) and content.strip():
                    ai_message = content
                elif isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        ai_message = " ".join(text_parts)
                    else:
                        ai_message = "I apologize, but I couldn't generate a response. Please try again."
                else:
                    ai_message = "I apologize, but I couldn't generate a response. Please try again."
            else:
                ai_message = "I apologize, but I couldn't generate a response. Please try again."
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected LLM response structure: {exc}") from exc
    
    return {"reply": ai_message}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    messages = build_langchain_messages(request.message, request.history)

    async def event_generator():
        inputs = {"messages": messages}
        full_message = ""
        try:
            async for event in agent.astream_events(inputs, version="v1"):
                if event.get("event") == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk is None:
                        continue

                    delta_text = ""
                    content = getattr(chunk, "content", None)

                    if isinstance(content, list):
                        for part in content:
                            text = getattr(part, "text", None)
                            if text:
                                delta_text += text
                    elif isinstance(content, str):
                        delta_text = content

                    if not delta_text:
                        continue

                    full_message += delta_text
                    yield json.dumps({"type": "token", "token": delta_text}) + "\n"
        except Exception as exc:
            yield json.dumps({"type": "error", "error": f"LLM stream failed: {exc}"}) + "\n"
            return

        if full_message:
            yield json.dumps({"type": "complete", "message": full_message}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    raw = await file.read()
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(io.BytesIO(raw)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Speech recognition service error: {exc}")

    return {"transcript": text}


@app.post("/voice/chat")
async def voice_chat(
    file: UploadFile = File(...),
    history: Optional[str] = Form(default=None),
):
    raw = await file.read()
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(io.BytesIO(raw)) as source:
            audio = recognizer.record(source)
        transcript = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Speech recognition service error: {exc}")

    history_messages: List[ChatMessage] = []
    if history:
        try:
            raw_history = json.loads(history)
            if isinstance(raw_history, list):
                for item in raw_history:
                    if not isinstance(item, dict):
                        continue
                    role = item.get("role")
                    content = item.get("content", "")
                    if role in ("user", "assistant") and isinstance(content, str):
                        history_messages.append(ChatMessage(role=role, content=content))
        except json.JSONDecodeError:
            history_messages = []

    messages = build_langchain_messages(transcript, history_messages)
    inputs = {"messages": messages}
    try:
        # Add timeout to prevent hanging (90 seconds should be enough for tool calls + response)
        result = await asyncio.wait_for(agent.ainvoke(inputs), timeout=90.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out. The agent took too long to respond.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc
    
    try:
        # Find the last AIMessage in the result (not just the last message, which might be a ToolMessage)
        ai_message = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, "content") and msg.content:
                # Check if content is a string and not empty
                content = msg.content
                if isinstance(content, str) and content.strip():
                    ai_message = content
                    break
                elif isinstance(content, list):
                    # Handle case where content might be a list of content blocks
                    text_parts = []
                    for part in content:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        ai_message = " ".join(text_parts)
                        break
        
        if ai_message is None or not ai_message.strip():
            # Fallback: try to get content from last message anyway
            last_msg = result["messages"][-1]
            if hasattr(last_msg, "content"):
                content = last_msg.content
                if isinstance(content, str) and content.strip():
                    ai_message = content
                elif isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        ai_message = " ".join(text_parts)
                    else:
                        ai_message = "I apologize, but I couldn't generate a response. Please try again."
                else:
                    ai_message = "I apologize, but I couldn't generate a response. Please try again."
            else:
                ai_message = "I apologize, but I couldn't generate a response. Please try again."
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected LLM response structure: {exc}") from exc

    return {"transcript": transcript, "reply": ai_message}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000)

