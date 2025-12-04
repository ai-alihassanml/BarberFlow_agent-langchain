from typing import List, Optional
from models.barber import Barber
from config.database import get_database
from bson import ObjectId
import difflib

async def get_all_barbers() -> List[Barber]:
    """Get all barbers."""
    db = get_database()
    cursor = db.barbers.find({"is_available": True})
    barbers = []
    async for doc in cursor:
        barbers.append(Barber(**doc))
    return barbers

async def get_barber_by_id(barber_id: str) -> Optional[Barber]:
    """Get specific barber."""
    db = get_database()
    doc = await db.barbers.find_one({"_id": barber_id})
    if doc:
        return Barber(**doc)
    return None

async def get_barbers_by_specialty(specialty: str) -> List[Barber]:
    """Filter barbers by specialty."""
    db = get_database()
    # Case insensitive search
    cursor = db.barbers.find({
        "specialties": {"$regex": specialty, "$options": "i"},
        "is_available": True
    })
    barbers = []
    async for doc in cursor:
        barbers.append(Barber(**doc))
    return barbers

async def get_barber_by_name(name: str) -> Optional[Barber]:
    """
    Find a barber by name with fuzzy matching.
    Handles partial matches (e.g., "sara" matches "Sarah Davis").
    """
    if not name or not name.strip():
        return None
    
    db = get_database()
    name_lower = name.strip().lower()
    
    # First try exact match (case insensitive)
    doc = await db.barbers.find_one({
        "name": {"$regex": f"^{name_lower}$", "$options": "i"},
        "is_available": True
    })
    if doc:
        return Barber(**doc)
    
    # Try partial match - name contains the search term
    doc = await db.barbers.find_one({
        "name": {"$regex": name_lower, "$options": "i"},
        "is_available": True
    })
    if doc:
        return Barber(**doc)
    
    # Try matching first or last name separately
    # Split the search term into words
    search_words = name_lower.split()
    if search_words:
        # Try to match any word in the barber's name
        for search_word in search_words:
            cursor = db.barbers.find({
                "name": {"$regex": search_word, "$options": "i"},
                "is_available": True
            })
            async for doc in cursor:
                barber = Barber(**doc)
                # Check if any word in barber's name matches any search word
                barber_words = barber.name.lower().split()
                if any(sw in bw or bw in sw for sw in search_words for bw in barber_words):
                    return barber

    # As a final fallback, use simple similarity matching on full names.
    # This helps with minor typos like "jone" for "John Smith".
    candidates: List[Barber] = []
    cursor = db.barbers.find({"is_available": True})
    async for doc in cursor:
        candidates.append(Barber(**doc))

    if not candidates:
        return None

    names = [b.name for b in candidates]
    # Get the closest match above a reasonable similarity cutoff
    best_matches = difflib.get_close_matches(name, names, n=1, cutoff=0.6)
    if not best_matches:
        return None

    best_name = best_matches[0]
    for barber in candidates:
        if barber.name == best_name:
            return barber

    return None