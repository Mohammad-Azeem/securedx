"""
SecureDx AI — Application Configuration

All settings are loaded from environment variables (and .env file in dev).
Sensitive values are never logged or exposed in API responses.
"""

from functools import lru_cache
import json
from typing import Literal
from urllib.parse import quote_plus
#from pydantic import AnyHttpUrl, Field, field_validator
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Clinic Identity ────────────────────────────────────────────────────────
    CLINIC_ID: str = Field(..., description="Unique clinic node identifier")
    CLINIC_NAME: str = Field(..., description="Human-readable clinic name")
    CLINIC_TIMEZONE: str = Field("America/New_York", description="Clinic timezone")

    # ── Environment ────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(..., min_length=32, description="JWT signing key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    #CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @property
    def cors_list(self) -> list[str]:
        #return [o.strip() for o in self.CORS_ORIGINS.split(",")]
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return []

        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except json.JSONDecodeError:
                # Fall back to comma-separated parsing if malformed JSON is provided.
                pass

        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    
    #@field_validator("CORS_ORIGINS", mode="before")
    #@classmethod
    #def parse_cors(cls, v):
    #    if isinstance(v, str):
    #        return [origin.strip() for origin in v.split(",")]
    #    return v
    
    #Support both comma-separated and JSON-array style origin formats.

        

    # ── Database ───────────────────────────────────────────────────────────────
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "securedx"
    DB_USER: str = "securedx_app"
    DB_PASSWORD: str = Field(..., description="PostgreSQL password")
    DB_ENCRYPTION_KEY: str = Field(..., min_length=32, description="pgcrypto AES-256 key")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    @property
    def DATABASE_URL(self) -> str:
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+asyncpg://{encoded_user}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync URL for Alembic migrations."""
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+psycopg2://{encoded_user}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── Keycloak ───────────────────────────────────────────────────────────────
    KEYCLOAK_SERVER_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "securedx"
    KEYCLOAK_CLIENT_ID: str = "securedx-api"
    KEYCLOAK_CLIENT_SECRET: str = Field(..., description="Keycloak client secret")

    @property
    def KEYCLOAK_OPENID_CONFIG_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/.well-known/openid-configuration"
        )

    @property
    def KEYCLOAK_JWKS_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/certs"
        )

    # ── Inference Engine ───────────────────────────────────────────────────────
    INFERENCE_SERVICE_URL: str = "http://inference:8001"
    INFERENCE_TIMEOUT_SECONDS: int = 10
    DIAGNOSIS_CONFIDENCE_THRESHOLD: float = Field(0.70, ge=0.0, le=1.0)
    MAX_DIFFERENTIALS: int = Field(5, ge=1, le=10)

    # ── Federated Learning ─────────────────────────────────────────────────────
    FL_ENABLED: bool = True

    # ── Audit Logging ──────────────────────────────────────────────────────────
    AUDIT_LOG_DIR: str = "/var/log/securedx/audit"
    AUDIT_LOG_RETENTION_DAYS: int = Field(2190, ge=2190)  # HIPAA: 6 years minimum
    AUDIT_FHIR_EXPORT_ENABLED: bool = True

    # ── De-identification ──────────────────────────────────────────────────────
    DEIDENTIFICATION_METHOD: Literal["safe_harbor", "expert_determination"] = "safe_harbor"
    PSEUDONYM_SALT: str = Field(..., min_length=16, description="Salt for pseudonymization")

    # ── Model Settings ─────────────────────────────────────────────────────────
    MODEL_PATH: str = "/models/securedx_v1.onnx"

    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance. Call get_settings() throughout the app."""
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()
