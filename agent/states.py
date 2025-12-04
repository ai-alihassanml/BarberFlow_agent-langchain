from typing import TypedDict, List, Optional, Dict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_intent: Optional[str]           # "book", "reschedule", "cancel", "inquiry"
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    selected_service: Optional[str]
    selected_barber: Optional[str]
    selected_datetime: Optional[datetime]
    available_slots: Optional[List[Dict]]
    booking_confirmed: bool
    appointment_id: Optional[str]
    current_step: str                    # Track conversation progress
