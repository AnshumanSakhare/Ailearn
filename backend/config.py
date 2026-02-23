"""
Centralised settings – loaded from environment / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Gemini
    GEMINI_API_KEY: str = ""
    CHAT_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/embedding-001"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_DB_URL: str = ""          # postgres connection string for vecs

    # App
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    FRONTEND_URL: str = ""           # Set to Vercel URL in production, e.g. https://your-app.vercel.app
    CHUNK_SIZE: int = 500              # tokens per chunk
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5                     # RAG retrieval count


settings = Settings()
