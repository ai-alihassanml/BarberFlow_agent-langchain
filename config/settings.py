from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str
    DATABASE_NAME: str = "barberflow"
    
    # Groq LLM (OpenAI-compatible)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str]
    GEMINI_MODEL: Optional[str] = "gemini-2.0-flash"
    
    # Application
    APP_NAME: str = "BarberFlow"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
