"""Core configuration settings."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    env: str = Field(default="development", description="Environment mode")
    
    # Database
    database_url: str = Field(..., description="PostgreSQL async connection string")
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    
    # Security
    jwt_secret: str = Field(default="dev-secret-key", description="JWT secret key")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:5173", 
            "http://127.0.0.1:3838",
            "http://localhost:3838",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ],
        description="Allowed CORS origins"
    )
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "PEARL Backend"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()