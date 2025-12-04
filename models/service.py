from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class Service(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str  # "Haircut", "Beard Trim", "Shave", etc.
    description: str
    duration_minutes: int
    price: float
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
