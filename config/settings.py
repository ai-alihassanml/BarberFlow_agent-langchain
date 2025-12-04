from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str
    DATABASE_NAME: str = "barberflow"
    
    # Gemini AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Application
    APP_NAME: str = "BarberFlow"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
