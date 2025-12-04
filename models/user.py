from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    email: EmailStr
    phone: str
    appointment_history: List[str] = []  # List of appointment IDs
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
