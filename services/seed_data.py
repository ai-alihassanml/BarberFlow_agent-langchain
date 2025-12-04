from models.barber import Barber, WorkingHours
from models.service import Service
from config.database import get_database
import logging

logger = logging.getLogger(__name__)

async def seed_barbers():
    """Create sample barbers."""
    db = get_database()
    count = await db.barbers.count_documents({})
    
    if count == 0:
        logger.info("Seeding barbers...")
        
        default_hours = {
            "monday": WorkingHours(start="09:00", end="17:00"),
            "tuesday": WorkingHours(start="09:00", end="17:00"),
            "wednesday": WorkingHours(start="09:00", end="17:00"),
            "thursday": WorkingHours(start="09:00", end="17:00"),
            "friday": WorkingHours(start="09:00", end="17:00"),
            "saturday": WorkingHours(start="10:00", end="15:00"),
            "sunday": WorkingHours(start="00:00", end="00:00", is_off=True)
        }
        
        barbers = [
            Barber(
                name="John Smith",
                email="john@barberflow.com",
                phone="555-0101",
                specialties=["modern cuts", "fades"],
                working_hours=default_hours,
                rating=4.9
            ),
            Barber(
                name="Mike Johnson",
                email="mike@barberflow.com",
                phone="555-0102",
                specialties=["classic styles", "beard trims"],
                working_hours=default_hours,
                rating=5.0
            ),
            Barber(
                name="Sarah Davis",
                email="sarah@barberflow.com",
                phone="555-0103",
                specialties=["styling", "coloring"],
                working_hours=default_hours,
                rating=4.8
            )
        ]
        
        for barber in barbers:
            await db.barbers.insert_one(barber.model_dump(by_alias=True))
        logger.info("Barbers seeded successfully")

async def seed_services():
    """Create available services."""
    db = get_database()
    count = await db.services.count_documents({})
    
    if count == 0:
        logger.info("Seeding services...")
        services = [
            Service(name="Haircut", description="Standard haircut", duration_minutes=30, price=30.0),
            Service(name="Beard Trim", description="Beard grooming", duration_minutes=20, price=20.0),
            Service(name="Shave", description="Hot towel shave", duration_minutes=30, price=35.0),
            Service(name="Full Service", description="Haircut + Beard", duration_minutes=60, price=50.0)
        ]
        
        for service in services:
            await db.services.insert_one(service.model_dump(by_alias=True))
        logger.info("Services seeded successfully")

async def initialize_database():
    """Seed all initial data."""
    await seed_barbers()
    await seed_services()
