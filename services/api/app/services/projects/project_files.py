"""Filesystem cleanup under the shared data volume."""

import shutil
from pathlib import Path
from uuid import UUID

from app.configs.config import Settings

PROJECT_DIRS = ("results", "uploads", "reports")


def remove_project_dirs(settings: Settings, project_id: UUID) -> None:
    """Delete a project's results, uploads and reports directories."""
    for name in PROJECT_DIRS:
        shutil.rmtree(Path(settings.data_dir) / name / str(project_id), ignore_errors=True)
