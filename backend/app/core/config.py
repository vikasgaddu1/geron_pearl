"""Core configuration settings."""

from typing import List, Optional

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
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=15, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    # OAuth2 Providers
    google_client_id: Optional[str] = Field(default=None, description="Google OAuth2 client ID")
    google_client_secret: Optional[str] = Field(default=None, description="Google OAuth2 client secret")
    google_redirect_uri: Optional[str] = Field(default=None, description="Google OAuth2 redirect URI")
    
    microsoft_client_id: Optional[str] = Field(default=None, description="Microsoft OAuth2 client ID")
    microsoft_client_secret: Optional[str] = Field(default=None, description="Microsoft OAuth2 client secret")
    microsoft_tenant_id: Optional[str] = Field(default="common", description="Microsoft tenant ID")
    microsoft_redirect_uri: Optional[str] = Field(default=None, description="Microsoft OAuth2 redirect URI")
    
    github_client_id: Optional[str] = Field(default=None, description="GitHub OAuth2 client ID")
    github_client_secret: Optional[str] = Field(default=None, description="GitHub OAuth2 client secret")
    github_redirect_uri: Optional[str] = Field(default=None, description="GitHub OAuth2 redirect URI")
    
    # Email (for password reset)
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(default="noreply@pearl.local", description="From email address")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:3001",
            "http://localhost:5173", 
            "http://127.0.0.1:3838",
            "http://localhost:3838",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
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