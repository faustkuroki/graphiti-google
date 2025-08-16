import os
from typing import Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    google_api_key: str
    openai_api_key: str
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    
    # Gemini Configuration
    gemini_model: str = "gemini-1.5-pro"
    gemini_temperature: float = 0.1
    gemini_max_tokens: Optional[int] = None
    
    # Concurrency Settings
    semaphore_limit: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # Feature Flags
    use_parallel_runtime: bool = False
    graphiti_telemetry_enabled: bool = False
    
    @validator('google_api_key', 'openai_api_key', 'neo4j_password')
    def validate_required_keys(cls, v):
        if not v:
            raise ValueError('Required API key or password is missing')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
