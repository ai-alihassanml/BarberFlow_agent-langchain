from langchain_core.tools import tool
from typing import List, Dict, Optional
from datetime import datetime
from services.barber_service import get_all_barbers, get_barbers_by_specialty, get_barber_by_id, get_barber_by_name
from services.availability_service import get_available_slots, check_slot_availability
from services.appointment_service import create_appointment, get_appointments_by_email, cancel_appointment
from services.seed_data import get_database # Access DB for services
from models.appointment import Appointment
from utils.datetime_utils import parse_natural_datetime

@tool
async def search_barbers(specialty: Optional[str] = None) -> List[Dict]:
    """
    Search for available barbers. Use this when user asks about available barbers or wants to see barber options.
    
    Args:
        specialty: Optional specialty to filter by (e.g., "haircut", "beard trim", "styling")
    
    Returns:
        List of barber dictionaries with id, name, specialties, and other details
    """
    if specialty:
        barbers = await get_barbers_by_specialty(specialty)
    else:
        barbers = await get_all_barbers()
        
    return [b.model_dump() for b in barbers]

@tool
async def check_slots(barber_id: str, date_str: str) -> List[Dict]:
    """
    Check all available time slots for a barber on a specific date.
    Use this when user wants to see all available times for a barber on a particular day.
    Handles barber name resolution (e.g., "john" matches "John Smith").
    
    Args:
        barber_id: ID of the barber OR barber name (e.g., "John", "John Smith", "john")
        date_str: Date string (e.g., "2025-12-05", "December 3, 2025", "3 dec 2025", "tomorrow")
    
    Returns:
        List of available time slots with formatted time strings. 
        Each slot has "time" (datetime) and "formatted" (string) fields.
        Returns empty list if barber not found, date invalid, or no slots available.
    """
    # Resolve barber - try by ID first, then by name
    barber = await get_barber_by_id(barber_id)
    if not barber:
        barber = await get_barber_by_name(barber_id)
    
    if not barber:
        return []
    
    dt = parse_natural_datetime(date_str)
    if not dt:
        return []
        
    slots = await get_available_slots(barber.id, dt)
    return slots

@tool
async def book_appointment(
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    barber_id: str,
    barber_name: str,
    service_type: str,
    datetime_str: str
) -> Dict:
    """
    Create a new appointment. This tool validates availability before booking.
    Always returns appointment_id (confirmation number) on success.
    If the requested time slot is unavailable, returns error with alternative time slots.
    
    Args:
        customer_name: Customer's full name
        customer_email: Customer's email address
        customer_phone: Customer's phone number
        barber_id: Barber's ID (can also be a name - will be resolved)
        barber_name: Barber's name (for display)
        service_type: Type of service (e.g., "haircut", "beard trim")
        datetime_str: Date and time string (e.g., "3 dec 2025 at 6pm")
    """
    # Parse datetime
    dt = parse_natural_datetime(datetime_str)
    if not dt:
        return {"success": False, "error": "Invalid date format", "appointment_id": None}
    
    # Resolve barber - try by ID first, then by name
    barber = await get_barber_by_id(barber_id)
    if not barber:
        # Try to find by name if barber_id might actually be a name
        barber = await get_barber_by_name(barber_id)
        if barber:
            barber_id = barber.id
            barber_name = barber.name
    
    # If still no barber found, try using barber_name
    if not barber and barber_name:
        barber = await get_barber_by_name(barber_name)
        if barber:
            barber_id = barber.id
            barber_name = barber.name
    
    if not barber:
        return {
            "success": False,
            "error": f"Barber not found: {barber_id or barber_name}",
            "appointment_id": None
        }
    
    # Check availability for the requested time slot
    availability = await check_slot_availability(barber_id, dt, duration=30)
    
    if not availability["available"]:
        # Format alternatives for response
        alternatives = []
        if availability.get("alternatives"):
            for alt in availability["alternatives"]:
                if isinstance(alt, dict):
                    dt_value = None
                    if "time" in alt and isinstance(alt["time"], datetime):
                        dt_value = alt["time"]
                    elif "datetime" in alt and isinstance(alt["datetime"], datetime):
                        dt_value = alt["datetime"]

                    if dt_value:
                        alternatives.append({
                            "time": dt_value.strftime("%I:%M %p"),
                            "datetime": dt_value.isoformat(),
                        })
                    elif "formatted" in alt:
                        alternatives.append({
                            "time": alt["formatted"],
                            "datetime": None,
                        })
                else:
                    alternatives.append({
                        "time": str(alt),
                        "datetime": None,
                    })
        
        return {
            "success": False,
            "error": availability["reason"],
            "appointment_id": None,
            "alternatives": alternatives,
            "barber_name": barber_name
        }
    
    # Slot is available, create appointment
    try:
        appt = Appointment(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            barber_id=barber_id,
            barber_name=barber_name,
            service_type=service_type,
            appointment_datetime=dt,
            duration_minutes=30 # Default
        )
        
        appt_id = await create_appointment(appt)
        return {
            "success": True,
            "appointment_id": appt_id,
            "confirmation_number": appt_id,  # Explicit confirmation number field
            "details": appt.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create appointment: {str(e)}",
            "appointment_id": None
        }

@tool
async def check_specific_slot(barber_name_or_id: str, datetime_str: str) -> Dict:
    """
    Check if a specific time slot is available for a barber.
    Returns availability status and suggests alternative time slots if unavailable.
    Handles barber name resolution (e.g., "sara" matches "Sarah Davis").
    
    Use this tool when a user requests booking at a specific time to verify availability
    before attempting to book.
    
    Args:
        barber_name_or_id: Barber's name (e.g., "Sarah Davis", "sara") or ID
        datetime_str: Date and time string (e.g., "3 dec 2025 at 6pm", "December 3, 2025 6:00 PM")
    
    Returns:
        Dictionary with availability status, reason, and alternative slots if unavailable
    """
    # Parse datetime
    dt = parse_natural_datetime(datetime_str)
    if not dt:
        return {
            "available": False,
            "error": "Invalid date format",
            "alternatives": []
        }
    
    # Resolve barber - try by ID first, then by name
    barber = await get_barber_by_id(barber_name_or_id)
    if not barber:
        barber = await get_barber_by_name(barber_name_or_id)
    
    if not barber:
        return {
            "available": False,
            "error": f"Barber not found: {barber_name_or_id}",
            "alternatives": []
        }
    
    # Check availability
    availability = await check_slot_availability(barber.id, dt, duration=30)
    
    # Format response with barber info
    result = {
        "available": availability["available"],
        "barber_id": barber.id,
        "barber_name": barber.name,
        "requested_time": dt.strftime("%B %d, %Y at %I:%M %p"),
        "reason": availability.get("reason", "Unknown"),
    }
    
    # Format alternatives
    if availability.get("alternatives"):
        formatted_alternatives = []
        for alt in availability["alternatives"]:
            if isinstance(alt, dict):
                dt_value = None
                if "time" in alt and isinstance(alt["time"], datetime):
                    dt_value = alt["time"]
                elif "datetime" in alt and isinstance(alt["datetime"], datetime):
                    dt_value = alt["datetime"]

                if dt_value:
                    formatted_alternatives.append({
                        "time": dt_value.strftime("%I:%M %p"),
                        "datetime": dt_value.isoformat(),
                    })
                elif "formatted" in alt:
                    formatted_alternatives.append({
                        "time": alt["formatted"],
                        "datetime": None,
                    })
            else:
                formatted_alternatives.append({
                    "time": str(alt),
                    "datetime": None,
                })

        result["alternatives"] = formatted_alternatives
    else:
        result["alternatives"] = []
    
    return result

@tool
async def my_appointments(email: str) -> List[Dict]:
    """
    Get all appointments for a customer by their email address.
    Use this when user asks to view their appointments or booking history.
    
    Args:
        email: Customer's email address
    
    Returns:
        List of appointment dictionaries with all booking details
    """
    appts = await get_appointments_by_email(email)
    return [a.model_dump() for a in appts]
