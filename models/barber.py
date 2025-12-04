from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from bson import ObjectId

class WorkingHours(BaseModel):
    start: str  # "09:00"
    end: str    # "17:00"
    is_off: bool = False

class Barber(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    email: EmailStr
    phone: str
    specialties: List[str]  # e.g., ["haircut", "beard_trim", "shave"]
    working_hours: Dict[str, WorkingHours]  # Day of week (lowercase) -> hours
    rating: float = 5.0
    is_available: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
