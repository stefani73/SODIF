"""Unit tests for safe application settings."""

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from sodif.settings import AppSettings, GatewaySettings, ModuleSettings, load_settings


def test_default_settings_are_product_safe(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SODIF_APP_NAME", raising=False)
    monkeypatch.delenv("SODIF_TAGLINE", raising=False)
    monkeypatch.delenv("SODIF_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SODIF_RELEASE", raising=False)
    monkeypatch.delenv("SODIF_ARCHIVE_ROOT", raising=False)
    monkeypatch.delenv("SODIF_EXPORT_ROOT", raising=False)
    monkeypatch.delenv("SODIF_MODULE_SECURITY_ENABLED", raising=False)
    monkeypatch.delenv("SODIF_MODULE_ARCHIVE_ENABLED", raising=False)
    monkeypatch.delenv("SODIF_MODULE_GATEWAY_ENABLED", raising=False)
    monkeypatch.delenv("SODIF_GATEWAY_ROUTE_ID", raising=False)
    monkeypatch.delenv("SODIF_GATEWAY_AUDIENCE", raising=False)
    monkeypatch.delenv("SODIF_GATEWAY_PATH_PREFIX", raising=False)
    monkeypatch.delenv("SODIF_GATEWAY_MAXIMUM_PARAMETERS", raising=False)
    monkeypatch.delenv("SODIF_ORGANIZATION_NAME", raising=False)
    monkeypatch.delenv("SODIF_WORKSPACE_NAME", raising=False)
    monkeypatch.delenv("SODIF_DOMAIN_NAME", raising=False)
    monkeypatch.delenv("SODIF_PROTECTED_SERVICE", raising=False)
    settings = load_settings()

    assert settings == AppSettings(
        app_name="SODIF",
        tagline="Exact ceea ce s-a semnat. O singură dată.",
        environment="local",
        release="0.18.0-product4",
        archive_root=Path("var/archive"),
        export_root=Path("var/exports"),
        modules=ModuleSettings(),
        gateway=GatewaySettings(),
    )


def test_settings_accept_non_secret_environment_overrides(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SODIF_ENVIRONMENT", "test")
    monkeypatch.setenv("SODIF_RELEASE", "quality-gate")
    monkeypatch.setenv("SODIF_ARCHIVE_ROOT", "var/test-archive")
    monkeypatch.setenv("SODIF_EXPORT_ROOT", "var/test-exports")
    monkeypatch.setenv("SODIF_MODULE_ARCHIVE_ENABLED", "off")
    monkeypatch.setenv("SODIF_MODULE_GATEWAY_ENABLED", "YES")
    monkeypatch.setenv("SODIF_GATEWAY_ROUTE_ID", "finance.approvals")
    monkeypatch.setenv("SODIF_GATEWAY_AUDIENCE", "finance-api")
    monkeypatch.setenv("SODIF_GATEWAY_PATH_PREFIX", "/approvals")
    monkeypatch.setenv("SODIF_GATEWAY_MAXIMUM_PARAMETERS", "24")
    monkeypatch.setenv("SODIF_ORGANIZATION_NAME", "PowerNet Labs")
    monkeypatch.setenv("SODIF_DOMAIN_NAME", "Plăți aprobate")

    settings = load_settings()

    assert settings.environment == "test"
    assert settings.release == "quality-gate"
    assert settings.archive_root == Path("var/test-archive")
    assert settings.export_root == Path("var/test-exports")
    assert settings.profile.organization_name == "PowerNet Labs"
    assert settings.profile.domain_name == "Plăți aprobate"
    assert settings.modules.archive_enabled is False
    assert settings.modules.gateway_enabled is True
    assert settings.gateway == GatewaySettings(
        route_id="finance.approvals",
        audience="finance-api",
        path_prefix="/approvals",
        maximum_parameters=24,
    )


def test_settings_reject_ambiguous_module_flags(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SODIF_MODULE_GATEWAY_ENABLED", "sometimes")

    with pytest.raises(ValueError, match="SODIF_MODULE_GATEWAY_ENABLED"):
        load_settings()


def test_module_settings_reject_unknown_module_keys() -> None:
    with pytest.raises(ValueError, match="Unknown product module"):
        ModuleSettings().is_enabled("unknown")


def test_gateway_settings_reject_invalid_policy_values(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SODIF_GATEWAY_MAXIMUM_PARAMETERS", "many")
    with pytest.raises(ValueError, match="must be an integer"):
        load_settings()

    with pytest.raises(ValueError, match="path prefix"):
        GatewaySettings(path_prefix="purchase-orders")
