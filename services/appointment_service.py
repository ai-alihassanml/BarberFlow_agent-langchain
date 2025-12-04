from typing import List, Optional
from datetime import datetime
from models.appointment import Appointment
from config.database import get_database
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

async def create_appointment(appointment: Appointment) -> str:
    """Create new appointment."""
    db = get_database()
    result = await db.appointments.insert_one(appointment.model_dump(by_alias=True))
    return str(result.inserted_id)

async def get_appointments_by_email(email: str) -> List[Appointment]:
    """Get all appointments for a customer."""
    db = get_database()
    cursor = db.appointments.find({"customer_email": email}).sort("appointment_datetime", 1)
    appointments = []
    async for doc in cursor:
        appointments.append(Appointment(**doc))
    return appointments

async def cancel_appointment(appointment_id: str) -> bool:
    """Cancel an appointment."""
    db = get_database()
    result = await db.appointments.update_one(
        {"_id": appointment_id},
        {"$set": {"status": "cancelled"}}
    )
    return result.modified_count > 0

async def get_barber_appointments(barber_id: str, start_date: datetime, end_date: datetime) -> List[Appointment]:
    """Get appointments for a barber within a date range."""
    db = get_database()
    cursor = db.appointments.find({
        "barber_id": barber_id,
        "status": "confirmed",
        "appointment_datetime": {
            "$gte": start_date,
            "$lte": end_date
        }
    })
    appointments = []
    async for doc in cursor:
        appointments.append(Appointment(**doc))
    return appointments
