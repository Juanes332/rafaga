"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings sourced from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Ráfaga API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Both are required: boot fails loudly when the environment lacks them.
    database_url: str
    jwt_secret: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = Field(default=720, gt=0)

    # Insert-if-absent seed; ignored unless both values are non-empty.
    admin_email: str = ""
    admin_password: str = ""

    # ADR-26: tier 1 by address, tier 2 by principal, plus two budgets.
    rate_limit_anon_per_minute: int = Field(default=120, gt=0)
    rate_limit_per_minute: int = Field(default=600, gt=0)
    rate_limit_login_per_minute: int = Field(default=10, gt=0)
    rate_limit_tiles_per_minute: int = Field(default=1500, gt=0)
    trust_proxy: bool = False
    rate_limit_storage_uri: str = "memory://"

    allowed_origins: str = ""
    data_dir: str = "/data"

    tile_url_template: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    tile_user_agent: str = "Rafaga/1.0 (local urban wind screening)"
    tile_cache_max_mb: int = Field(default=500, gt=0)
    tile_cache_min_ttl_days: int = 7

    geocoding_url: str = Field(
        default="https://geocoding-api.open-meteo.com/v1/search",
        validation_alias=AliasChoices("OPEN_METEO_GEOCODING_URL", "GEOCODING_URL"),
    )
    elevation_url: str = Field(
        default="https://api.open-meteo.com/v1/elevation",
        validation_alias=AliasChoices("OPEN_METEO_ELEVATION_URL", "ELEVATION_URL"),
    )
    archive_url: str = Field(
        default="https://archive-api.open-meteo.com/v1/archive",
        validation_alias=AliasChoices("OPEN_METEO_ARCHIVE_URL", "ARCHIVE_URL"),
    )
    external_timeout_s: float = 20.0

    alternatives_limit_default: int = Field(default=8, ge=1, le=20)
    job_retention_days: int = 90
    facade_envelope_m: float = 10.0
    max_geometry_upload_mb: int = Field(
        default=100, validation_alias=AliasChoices("MAX_UPLOAD_GEOMETRY_MB")
    )
    max_image_upload_mb: int = Field(
        default=25, validation_alias=AliasChoices("MAX_UPLOAD_IMAGE_MB")
    )
    max_payload_mb: int = 20
    cpu_max_nodes_3d: int = Field(default=3_000_000, gt=0)

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str) -> str:
        """Accept plain postgresql:// URLs by selecting the psycopg driver."""
        for plain in ("postgresql://", "postgres://"):
            if value.startswith(plain):
                return "postgresql+psycopg://" + value[len(plain):]
        return value

    @property
    def origins(self) -> list[str]:
        """Return the CORS origins as a clean list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, avoiding env re-reads."""
    return Settings()
