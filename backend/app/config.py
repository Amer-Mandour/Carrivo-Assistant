"""
Application settings using Pydantic
"""

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum

class Language(str, Enum):
    ARABIC_EGYPTIAN = "ar_EG"
    ARABIC = "ar"
    ENGLISH = "en"

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    
    # LLM Settings
    openrouter_api_key: str
    openrouter_model: str = "llama-3.1-8b-instant"
    
    # Application
    app_name: str = "Carrivo Assistant"
    app_env: str = "development"
    debug: bool = True
    
    # Features
    enable_arabic_slang: bool = True
    enable_auto_language_detection: bool = True
    
    # RAG Settings
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    
    # Rate Limiting
    rate_limit_per_minute: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 