"""Core configuration settings."""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    env: str = Field(default="development", description="Environment mode")
    
    # Database
    database_url: str = Field(..., description="PostgreSQL async connection string")
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    
    @field_validator('database_url', mode='after')
    @classmethod
    def convert_to_async_url(cls, v: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// for async support."""
        if v.startswith('postgresql://'):
            return v.replace('postgresql://', 'postgresql+asyncpg://', 1)
        return v
    
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
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP connection")
    
    # Frontend URL (for password reset links)
    frontend_url: str = Field(default="http://localhost:5173", description="Frontend base URL")
    
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
    
    # ===========================================
    # Multi-Tenancy / SaaS Configuration
    # ===========================================
    
    # Stripe Integration
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_publishable_key: Optional[str] = Field(default=None, description="Stripe publishable key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook secret")
    
    # Stripe Price IDs for subscription tiers
    stripe_price_starter: Optional[str] = Field(default=None, description="Stripe price ID for Starter plan")
    stripe_price_professional: Optional[str] = Field(default=None, description="Stripe price ID for Professional plan")
    stripe_price_enterprise: Optional[str] = Field(default=None, description="Stripe price ID for Enterprise plan")
    
    # Subscription settings
    trial_period_days: int = Field(default=30, description="Trial period in days")
    subscription_grace_period_days: int = Field(default=7, description="Grace period for past_due subscriptions")
    
    # Super Admin (separate from regular JWT)
    super_admin_jwt_secret: str = Field(
        default="super-admin-dev-secret-change-in-production",
        description="Separate JWT secret for super admin tokens"
    )
    super_admin_token_expire_hours: int = Field(default=4, description="Super admin token expiration in hours")
    super_admin_email: str = Field(
        default="superadmin@pearl.local",
        description="Default super admin email"
    )
    
    # Email Provider (for SaaS transactional emails)
    email_provider: str = Field(default="smtp", description="Email provider: smtp, sendgrid, ses")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per tenant per minute")
    
    # Application version
    app_version: str = Field(default="1.0.0", description="Application version")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()