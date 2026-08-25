"""Unit tests for safe application settings."""

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from sodif.settings import AppSettings, load_settings


def test_default_settings_are_product_safe(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SODIF_APP_NAME", raising=False)
    monkeypatch.delenv("SODIF_TAGLINE", raising=False)
    monkeypatch.delenv("SODIF_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SODIF_RELEASE", raising=False)
    monkeypatch.delenv("SODIF_ARCHIVE_ROOT", raising=False)
    settings = load_settings()

    assert settings == AppSettings(
        app_name="SODIF",
        tagline="Exact ceea ce s-a semnat. O singură dată.",
        environment="local",
        release="0.14.0-dms5",
        archive_root=Path("var/archive"),
    )


def test_settings_accept_non_secret_environment_overrides(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SODIF_ENVIRONMENT", "test")
    monkeypatch.setenv("SODIF_RELEASE", "quality-gate")
    monkeypatch.setenv("SODIF_ARCHIVE_ROOT", "var/test-archive")

    settings = load_settings()

    assert settings.environment == "test"
    assert settings.release == "quality-gate"
    assert settings.archive_root == Path("var/test-archive")
