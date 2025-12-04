from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class Appointment(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    barber_id: str
    barber_name: str
    service_type: str
    appointment_datetime: datetime
    duration_minutes: int
    status: str = "confirmed"  # "confirmed", "cancelled", "completed"
    created_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
