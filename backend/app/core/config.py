from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Known development defaults and placeholder secrets that must never be permitted in production
INSECURE_DEV_SECRETS: Set[str] = {
    "reliefos-kamrup-metro-eoc-secret-key-2026",
    "reliefos-kamrup-metro-dev-only-fallback-key-2026",
    "secret",
    "change-me",
    "default-secret",
    "your_high_entropy_production_jwt_secret_here",
    "secret-key",
    "jwt-secret-key",
}

DEV_FALLBACK_JWT_SECRET: str = "reliefos-kamrup-metro-dev-only-fallback-key-2026"


class Settings(BaseSettings):
    PROJECT_NAME: str = "RELIEFOS Lite API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # "development", "testing", "staging", "production"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8013
    ALLOWED_ORIGINS: str = "http://localhost:3012,http://127.0.0.1:3012"
    # Database Configuration & Pool Sizing
    DATABASE_URL: str = "sqlite:///./reliefos_lite.db"
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 5432
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = Field(default=None, repr=False)
    DB_NAME: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # AI Infrastructure Configuration (Backend-Only Credentials)
    AI_PROVIDER: str = "mock"  # "gemini", "openai", "mock"
    AI_COPILOT_PROVIDER: Optional[str] = None
    GEMINI_API_KEY: str = Field(default="", repr=False)
    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    OPENAI_API_KEY: str = Field(default="", repr=False)
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_TIMEOUT_SECONDS: float = 15.0
    AI_MAX_RETRIES: int = 2
    AI_RATE_LIMIT_PER_MINUTE: int = 30
    AI_TEMPERATURE: float = 0.2

    # Authentication & Security
    AUTH_ENABLED: bool = True
    AUTH_STRICT: bool = False
    JWT_SECRET: Optional[str] = Field(default=None, repr=False)
    JWT_SECRET_KEY: Optional[str] = Field(default=None, repr=False)
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRY_HOURS: int = 24

    @property
    def is_production(self) -> bool:
        env = (self.ENVIRONMENT or "").strip().lower()
        if env in ("production", "prod"):
            return True
        if not self.DEBUG and env not in ("development", "dev", "test", "testing"):
            return True
        return False

    @property
    def is_sqlite(self) -> bool:
        url = (self.DATABASE_URL or "").strip().lower()
        return url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        url = (self.DATABASE_URL or "").strip().lower()
        return (
            url.startswith("postgres://")
            or url.startswith("postgresql://")
            or url.startswith("postgresql+")
        )

    @property
    def normalized_database_url(self) -> str:
        url = (self.DATABASE_URL or "").strip()
        if not url:
            if self.is_production:
                if self.DB_HOST and self.DB_USER and self.DB_NAME:
                    pwd = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
                    port = f":{self.DB_PORT}" if self.DB_PORT else ""
                    return f"postgresql+psycopg2://{self.DB_USER}{pwd}@{self.DB_HOST}{port}/{self.DB_NAME}"
                raise ValueError("DATABASE_URL or DB_HOST/DB_USER/DB_NAME must be specified in production.")
            url = "sqlite:///./reliefos_lite.db"
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith("sqlite:///./"):
            backend_dir = Path(__file__).resolve().parent.parent.parent
            db_file = url.replace("sqlite:///./", "")
            return f"sqlite:///{(backend_dir / db_file).as_posix()}"
        return url

    @property
    def database_engine_type(self) -> str:
        if self.is_postgres:
            return "postgresql"
        if self.is_sqlite:
            return "sqlite"
        return "other"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def get_jwt_secret(self) -> str:
        """
        Returns the active validated JWT secret.
        Fails safely if required secret is missing or insecure in production.
        """
        if self.is_production:
            if not self.JWT_SECRET or not self.JWT_SECRET.strip():
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a secure, "
                    "cryptographically random JWT_SECRET configured via environment variable. "
                    "No JWT_SECRET was provided."
                )
            clean_secret = self.JWT_SECRET.strip()
            if clean_secret in INSECURE_DEV_SECRETS:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment rejected an insecure default JWT_SECRET. "
                    "Please provide a unique, cryptographically random secret in production."
                )
            if len(clean_secret) < 32:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a JWT_SECRET of at least "
                    "32 characters. Provided secret is too short."
                )
            return clean_secret

        return self.JWT_SECRET or DEV_FALLBACK_JWT_SECRET

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        if not self.JWT_SECRET and self.JWT_SECRET_KEY:
            self.JWT_SECRET = self.JWT_SECRET_KEY
        if self.AI_COPILOT_PROVIDER and self.AI_PROVIDER == "mock":
            self.AI_PROVIDER = self.AI_COPILOT_PROVIDER

        if self.is_production:
            if not self.JWT_SECRET or not self.JWT_SECRET.strip():
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a secure, "
                    "cryptographically random JWT_SECRET configured via environment variable. "
                    "No JWT_SECRET was provided."
                )
            clean_secret = self.JWT_SECRET.strip()
            if clean_secret in INSECURE_DEV_SECRETS:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment rejected an insecure default JWT_SECRET. "
                    "Please provide a unique, cryptographically random secret in production."
                )
            if len(clean_secret) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a JWT_SECRET of at least "
                    "32 characters. Provided secret is too short."
                )
            if not self.AUTH_STRICT:
                self.AUTH_STRICT = True

            # 2. Database Dialect Validation for Production
            if not self.DATABASE_URL or not self.DATABASE_URL.strip():
                if self.DB_HOST and self.DB_USER and self.DB_NAME:
                    pwd = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
                    port = f":{self.DB_PORT}" if self.DB_PORT else ""
                    self.DATABASE_URL = f"postgresql+psycopg2://{self.DB_USER}{pwd}@{self.DB_HOST}{port}/{self.DB_NAME}"
                else:
                    raise ValueError(
                        "CRITICAL DATABASE CONFIGURATION ERROR: Production deployment requires a PostgreSQL database. "
                        "Please configure DATABASE_URL or DB_HOST/DB_USER/DB_NAME."
                    )
            elif self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
            elif self.DATABASE_URL.startswith("postgresql://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

            if self.is_sqlite:
                raise ValueError(
                    "CRITICAL DATABASE CONFIGURATION ERROR: Production deployment requires PostgreSQL for multi-worker concurrency. "
                    "SQLite is only permitted in development and test environments (ENVIRONMENT='development' or 'testing'). "
                    "Please configure DATABASE_URL (e.g., postgresql+psycopg2://user:pass@host:5432/reliefos_lite)."
                )
            if not self.is_postgres:
                raise ValueError(
                    "CRITICAL DATABASE CONFIGURATION ERROR: Production database URL must use a supported PostgreSQL dialect "
                    "(e.g., postgresql+psycopg2://user:pass@host:5432/reliefos_lite)."
                )
        else:
            # Development / Testing mode: convenient fallback when secret is not configured
            if not self.JWT_SECRET or not self.JWT_SECRET.strip():
                self.JWT_SECRET = DEV_FALLBACK_JWT_SECRET
            # Standardize development URL if postgresql dialect given
            if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
            elif self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
