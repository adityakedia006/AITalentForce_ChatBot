from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    GROQ_API_KEY: str
    ELEVENLABS_API_KEY: str
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # LLM Configuration
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_SYSTEM_PROMPT: str = (
        "You are a helpful, friendly AI assistant. Be concise, clear, and proactive. "
        "If weather data is provided, present it conversationally. Avoid repetition."
    )
    # Alternative models: llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
    
    # ElevenLabs Configuration
    ELEVENLABS_MODEL: str = "scribe_v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
