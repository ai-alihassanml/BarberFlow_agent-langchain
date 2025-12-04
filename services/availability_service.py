from datetime import datetime, timedelta
from typing import List, Dict
from services.appointment_service import get_barber_appointments
from services.barber_service import get_barber_by_id
from utils.datetime_utils import get_day_name

async def get_available_slots(
    barber_id: str,
    date: datetime,
    service_duration: int = 30
) -> List[Dict]:
    """
    Calculate available time slots for a barber on a given date.
    """
    barber = await get_barber_by_id(barber_id)
    if not barber:
        return []

    # Get working hours for the day
    day_name = get_day_name(date)
    if day_name not in barber.working_hours:
        return []
    
    hours = barber.working_hours[day_name]
    if hours.is_off:
        return []

    # Parse working hours
    start_hour = int(hours.start.split(":")[0])
    start_minute = int(hours.start.split(":")[1])
    end_hour = int(hours.end.split(":")[0])
    end_minute = int(hours.end.split(":")[1])

    work_start = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    work_end = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    # Get existing appointments
    # Query for the whole day
    day_start = date.replace(hour=0, minute=0, second=0)
    day_end = date.replace(hour=23, minute=59, second=59)
    
    appointments = await get_barber_appointments(barber_id, day_start, day_end)
    
    # Calculate slots
    slots = []
    current_time = work_start
    
    while current_time + timedelta(minutes=service_duration) <= work_end:
        slot_end = current_time + timedelta(minutes=service_duration)
        
        # Check if slot overlaps with any appointment
        is_available = True
        for appt in appointments:
            # Simple overlap check
            # Appt start < Slot end AND Appt end > Slot start
            appt_end = appt.appointment_datetime + timedelta(minutes=appt.duration_minutes)
            if appt.appointment_datetime < slot_end and appt_end > current_time:
                is_available = False
                break
        
        # Also check if slot is in the past
        if date.date() == datetime.now().date():
            is_future = current_time > datetime.now()
        else:
            is_future = True

        if is_future and is_available:
            slots.append({
                "time": current_time,
                "formatted": current_time.strftime("%I:%M %p")
            })
            
        current_time += timedelta(minutes=30)  # 30 min intervals
        
    return slots

async def _get_next_available_slots(
    barber_id: str,
    start_date: datetime,
    service_duration: int = 30
) -> List[Dict]:
    date = start_date
    for _ in range(7):
        slots = await get_available_slots(barber_id, date, service_duration)
        if slots:
            return slots
        date = date + timedelta(days=1)
    return []

async def check_slot_availability(
    barber_id: str,
    slot_datetime: datetime,
    duration: int = 30
) -> Dict:
    """
    Check if a specific time slot is available for a barber.
    Returns a dictionary with availability status and alternative slots if unavailable.
    """
    barber = await get_barber_by_id(barber_id)
    if not barber:
        return {
            "available": False,
            "reason": "Barber not found",
            "alternatives": []
        }
    
    # Check if barber is available
    if not barber.is_available:
        return {
            "available": False,
            "reason": "Barber is not available",
            "alternatives": []
        }
    
    # Get working hours for the day
    day_name = get_day_name(slot_datetime)
    if day_name not in barber.working_hours:
        return {
            "available": False,
            "reason": f"Barber does not work on {day_name}",
            "alternatives": []
        }
    
    hours = barber.working_hours[day_name]
    if hours.is_off:
        return {
            "available": False,
            "reason": f"Barber is off on {day_name}",
            "alternatives": []
        }
    
    # Parse working hours
    start_hour = int(hours.start.split(":")[0])
    start_minute = int(hours.start.split(":")[1])
    end_hour = int(hours.end.split(":")[0])
    end_minute = int(hours.end.split(":")[1])
    
    work_start = slot_datetime.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    work_end = slot_datetime.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    # Check if slot is within working hours
    slot_end = slot_datetime + timedelta(minutes=duration)
    if slot_datetime < work_start or slot_end > work_end:
        # Get alternative slots for the same day or upcoming days when
        # the requested day is already in the past.
        if slot_datetime.date() < datetime.now().date():
            alternatives = await _get_next_available_slots(barber_id, datetime.now(), duration)
        else:
            alternatives = await get_available_slots(barber_id, slot_datetime, duration)

        return {
            "available": False,
            "reason": "Time slot is outside working hours",
            "alternatives": alternatives[:5]  # Return up to 5 alternatives
        }
    
    # Check if slot is in the past
    if slot_datetime < datetime.now():
        alternatives = await _get_next_available_slots(barber_id, datetime.now(), duration)
        return {
            "available": False,
            "reason": "Time slot is in the past",
            "alternatives": alternatives[:5]
        }
    
    # Get existing appointments for the day
    day_start = slot_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = slot_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    appointments = await get_barber_appointments(barber_id, day_start, day_end)
    
    # Check for conflicts with existing appointments
    for appt in appointments:
        appt_end = appt.appointment_datetime + timedelta(minutes=appt.duration_minutes)
        # Check if slots overlap: slot_start < appt_end AND slot_end > appt_start
        if slot_datetime < appt_end and slot_end > appt.appointment_datetime:
            # Slot is not available, get alternatives
            alternatives = await get_available_slots(barber_id, slot_datetime, duration)
            return {
                "available": False,
                "reason": "Time slot conflicts with existing appointment",
                "alternatives": alternatives[:5]  # Return up to 5 alternatives
            }
    
    # Slot is available
    return {
        "available": True,
        "reason": "Slot is available",
        "alternatives": []
    }