from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal
import asyncio
import io
import json

import speech_recognition as sr
from langchain_core.messages import HumanMessage, AIMessage

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
    result = await agent.ainvoke(inputs)
    ai_message = result["messages"][-1].content
    return {"reply": ai_message}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    messages = build_langchain_messages(request.message, request.history)

    async def event_generator():
        inputs = {"messages": messages}
        full_message = ""

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
async def voice_chat(file: UploadFile = File(...)):
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

    messages = build_langchain_messages(transcript, [])
    inputs = {"messages": messages}
    result = await agent.ainvoke(inputs)
    ai_message = result["messages"][-1].content

    return {"transcript": transcript, "reply": ai_message}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000)

