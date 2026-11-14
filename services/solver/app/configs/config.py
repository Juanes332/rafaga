"""Solver configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SOLVER_VERSION = "1.0.0"


class Settings(BaseSettings):
    """Centralized solver settings sourced from the environment."""

    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Rafaga solver"
    app_version: str = SOLVER_VERSION
    # Empty means "no database": /health reports it down and the
    # worker stays idle instead of crashing the process at boot.
    database_url: str = ""
    data_dir: str = "/data"
    rafaga_device: Literal["auto", "cpu", "gpu"] = "auto"
    gpu_memory_fraction: float = Field(default=0.85, gt=0, le=1)
    cpu_max_nodes_3d: int = Field(default=3_000_000, gt=0)
    light_lane_concurrency: int = Field(default=2, gt=0, le=16)
    log_level: str = "info"
    # The queue worker starts in the app lifespan; tests switch it off.
    worker_enabled: bool = True
    poll_interval_s: float = Field(default=2.0, gt=0)
    heartbeat_interval_s: float = Field(default=5.0, gt=0)
    orphan_timeout_s: float = Field(default=60.0, gt=0)
    cancel_kill_after_s: float = Field(default=8.0, gt=0)
    startup_benchmark: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, avoiding env re-reads."""
    return Settings()
