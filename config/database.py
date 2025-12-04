from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    """Initialize MongoDB connection."""
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI)
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        
        # Verify connection
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes for performance
        await _create_indexes()
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise e

async def _create_indexes():
    """Create necessary indexes."""
    try:
        # Appointments indexes
        await db_instance.db.appointments.create_index("appointment_datetime")
        await db_instance.db.appointments.create_index("customer_email")
        await db_instance.db.appointments.create_index("barber_id")
        
        # Barbers indexes
        await db_instance.db.barbers.create_index("is_available")
        
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

async def close_mongo_connection():
    """Close MongoDB connection."""
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed")

def get_database():
    """Get database instance."""
    return db_instance.db
