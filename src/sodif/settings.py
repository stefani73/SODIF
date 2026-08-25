"""Typed application settings with safe local defaults."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Immutable settings required by the application shell."""

    app_name: str
    tagline: str
    environment: str
    release: str
    archive_root: Path = Path("var/archive")


def load_settings() -> AppSettings:
    """Load non-secret settings from the environment."""
    return AppSettings(
        app_name=getenv("SODIF_APP_NAME", "SODIF"),
        tagline=getenv("SODIF_TAGLINE", "Exact ceea ce s-a semnat. O singură dată."),
        environment=getenv("SODIF_ENVIRONMENT", "local"),
        release=getenv("SODIF_RELEASE", "0.12.0-dms3"),
        archive_root=Path(getenv("SODIF_ARCHIVE_ROOT", "var/archive")),
    )
