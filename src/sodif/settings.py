"""Typed application settings with safe local defaults."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModuleSettings:
    """Product modules exposed by the application shell."""

    security_enabled: bool = True
    archive_enabled: bool = True
    gateway_enabled: bool = True

    def is_enabled(self, module_key: str) -> bool:
        """Return whether a known product module is enabled."""
        availability = {
            "security": self.security_enabled,
            "archive": self.archive_enabled,
            "gateway": self.gateway_enabled,
        }
        try:
            return availability[module_key]
        except KeyError as error:
            raise ValueError(f"Unknown product module: {module_key}") from error


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Immutable settings required by the application shell."""

    app_name: str
    tagline: str
    environment: str
    release: str
    archive_root: Path = Path("var/archive")
    modules: ModuleSettings = ModuleSettings()


def load_settings() -> AppSettings:
    """Load non-secret settings from the environment."""
    return AppSettings(
        app_name=getenv("SODIF_APP_NAME", "SODIF"),
        tagline=getenv("SODIF_TAGLINE", "Exact ceea ce s-a semnat. O singură dată."),
        environment=getenv("SODIF_ENVIRONMENT", "local"),
        release=getenv("SODIF_RELEASE", "0.15.0-platform1"),
        archive_root=Path(getenv("SODIF_ARCHIVE_ROOT", "var/archive")),
        modules=ModuleSettings(
            security_enabled=_environment_flag("SODIF_MODULE_SECURITY_ENABLED", True),
            archive_enabled=_environment_flag("SODIF_MODULE_ARCHIVE_ENABLED", True),
            gateway_enabled=_environment_flag("SODIF_MODULE_GATEWAY_ENABLED", True),
        ),
    )


def _environment_flag(name: str, default: bool) -> bool:
    """Parse an explicit boolean environment flag."""
    value = getenv(name)
    if value is None:
        return default
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")
