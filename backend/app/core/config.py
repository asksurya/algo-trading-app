"""
Application configuration using Pydantic settings.
All configuration is environment-driven - no hardcoded values.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    # Application
    APP_NAME: str = Field(default="Algo Trading API")
    APP_VERSION: str = Field(default="0.1.0")
    API_V1_STR: str = Field(default="/api/v1")
    ENVIRONMENT: str = Field(default="development")
    
    # Database
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )
    
    # Redis
    REDIS_URL: str = Field(
        ...,
        description="Redis connection URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT token generation"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    
    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed origins"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # Alpaca Trading
    ALPACA_API_KEY: str = Field(
        ...,
        description="Alpaca API key"
    )
    ALPACA_SECRET_KEY: str = Field(
        ...,
        description="Alpaca secret key"
    )
    ALPACA_BASE_URL: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Alpaca API base URL"
    )
    
    # Email (Optional)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: Optional[int] = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    EMAIL_FROM: str = Field(default="noreply@algo-trading.local")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT.lower() == "test"


# Global settings instance
settings = Settings()
