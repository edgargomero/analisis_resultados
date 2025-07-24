"""
CEAPSI Backend Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "CEAPSI Backend"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Config
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database Config
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    supabase_service_role_key: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # File Upload
    max_upload_size: int = Field(default=200 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 200MB
    allowed_file_types: List[str] = Field(
        default=[".csv", ".xlsx", ".xls"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Session Management
    session_timeout_days: int = Field(default=30, env="SESSION_TIMEOUT_DAYS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # External APIs
    reservo_api_url: str = Field(default="", env="RESERVO_API_URL")
    reservo_api_key: str = Field(default="", env="RESERVO_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()