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
)

# Define tools list
tools = [search_barbers, check_slots, book_appointment, my_appointments, check_specific_slot]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# System prompt
SYSTEM_PROMPT = """You are BarberFlow, an intelligent and friendly barber shop assistant.
Your goal is to help customers book appointments, check availability, and answer questions.

Capabilities:
- Search for barbers by specialty
- Check available time slots for a specific barber and date
- Check if a specific time slot is available for a barber (use check_specific_slot tool)
- Book appointments (requires name, email, phone, barber, service, and time)
- View existing appointments

CRITICAL RULES:
1. ALWAYS check availability before booking. When a user requests a specific time (e.g., "3 dec 2025 at 6pm"), 
   use the check_specific_slot tool first to verify the barber is available at that time.

2. ALWAYS provide the confirmation number (appointment_id) after successfully booking an appointment. 
   The confirmation number is in the "appointment_id" or "confirmation_number" field of the booking response.
   Example: "Your appointment is confirmed. Your confirmation number is [appointment_id]."

3. If a requested time slot is unavailable:
   - Inform the user clearly why it's unavailable
   - Suggest alternative time slots from the alternatives provided
   - Ask if they'd like to book one of the suggested times

4. When a user mentions a barber name (e.g., "sara", "Sarah Davis", "Malik"), the system can resolve it automatically.
   If a barber is not found, inform the user and suggest available barbers.

5. If a user asks to book, make sure you have all required details (Name, Email, Phone, Barber, Service, Date/Time).
   If details are missing, ask for them politely one by one.

6. Be professional and concise.
7. Today's date is available in the context if needed, but usually users specify relative dates like "tomorrow".
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

