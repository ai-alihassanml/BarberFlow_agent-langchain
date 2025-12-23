from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config.settings import settings
from agent.states import AgentState
from agent.tools import search_barbers, check_slots, book_appointment, my_appointments, check_specific_slot

# Initialize Groq LLM via OpenAI-compatible endpoint
llm = ChatOpenAI(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    temperature=0.2,
    max_tokens=200,  # Increased to ensure complete responses after tool calls
    timeout=30,  # Add timeout to prevent hanging
)

# Define tools list
tools = [search_barbers, check_slots, book_appointment, my_appointments, check_specific_slot]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# System prompt
SYSTEM_PROMPT = """You are BarberFlow, a barber shop assistant.

BE VERY BRIEF:
- Use a friendly, professional tone.
- Answer in 3-5 sentences only (around 60-120 words).
- Do not write long explanations, bullet lists, or multiple paragraphs unless explicitly asked.

You can:
- Search for barbers
- Check available time slots
- Check if a specific time is available (check_specific_slot)
- Book appointments (need: name, email, phone, barber, service, date/time)
- View appointments

CRITICAL RULES:
1. Check availability FIRST before booking a specific time using check_specific_slot.
2. After booking, ALWAYS provide a confirmation response with the confirmation number in format: "Confirmation: [number]".
3. After ANY tool call completes, you MUST generate a response to the user - never leave them without a reply.
4. If time unavailable, suggest ONE alternative time in a single short sentence.
5. If missing booking details, ask for ONE thing at a time in a short question.
6. Always keep responses SHORT, CLEAR, and PROFESSIONAL.
7. NEVER end a conversation without responding - always provide a final message after tool execution.
"""

async def call_model(state: AgentState):
    """
    Core agent node that calls the LLM.
    """
    messages = state["messages"]
    
    # Prepend system message if it's the first turn or ensure it's in context
    # LangGraph usually handles state updates, but we want to ensure the system prompt is active.
    # We can create a prompt template.
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm_with_tools
    
    # We pass the full message history
    response = await chain.ainvoke({"messages": messages})
    
    return {"messages": [response]}

