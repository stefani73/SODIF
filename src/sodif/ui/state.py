"""Session-scoped product state shared by Streamlit pages."""

from collections.abc import Callable
from pathlib import Path
from typing import cast
from uuid import uuid4

import streamlit as st

from sodif.demo.models import FlightConfiguration, FlightKind, FlightReport
from sodif.demo.runner import run_security_flight, run_transversal_memory_flight
from sodif.reporting import (
    FlightExports,
    PersistedFlightRun,
    build_flight_exports,
    persist_flight_run,
)
from sodif.settings import AppSettings

_REPORTS_KEY = "sodif_flight_reports"
_EXPORTS_KEY = "sodif_flight_exports"
_RUNNERS_KEY = "sodif_flight_runners"
_ACTIVE_KIND_KEY = "sodif_active_flight_kind"
_PROFILE_KEY = "sodif_operational_profile"
_EXPORT_ROOT_KEY = "sodif_export_root"
_PERSISTED_RUNS_KEY = "sodif_persisted_runs"


def initialize_operational_profile(settings: AppSettings) -> FlightConfiguration:
    """Return the current session profile, seeded from application settings."""
    profile = st.session_state.get(_PROFILE_KEY)
    if isinstance(profile, FlightConfiguration):
        return profile
    profile = _profile_from_settings(
        settings,
        session_id=f"session-{uuid4().hex[:12]}",
    )
    st.session_state[_PROFILE_KEY] = profile
    return profile


def save_operational_profile(profile: FlightConfiguration) -> None:
    """Save a validated profile for this session and invalidate stale run results."""
    st.session_state[_PROFILE_KEY] = profile
    for key in (
        _REPORTS_KEY,
        _EXPORTS_KEY,
        _ACTIVE_KIND_KEY,
        _PERSISTED_RUNS_KEY,
        _RUNNERS_KEY,
    ):
        st.session_state.pop(key, None)


def reset_operational_profile(settings: AppSettings) -> FlightConfiguration:
    """Restore preconfigured values while preserving the session identity."""
    current = initialize_operational_profile(settings)
    profile = _profile_from_settings(settings, session_id=current.session_id)
    save_operational_profile(profile)
    return profile


def _profile_from_settings(settings: AppSettings, *, session_id: str) -> FlightConfiguration:
    return FlightConfiguration(
        session_id=session_id,
        organization_name=settings.profile.organization_name,
        workspace_name=settings.profile.workspace_name,
        domain_name=settings.profile.domain_name,
        environment=settings.environment,
        protected_service=settings.profile.protected_service,
        route_id=settings.gateway.route_id,
        audience=settings.gateway.audience,
        path_prefix=settings.gateway.path_prefix,
        maximum_parameters=settings.gateway.maximum_parameters,
    )


def register_flight_runners(
    security: Callable[[], FlightReport],
    transversal: Callable[[], FlightReport],
    export_root: Path = Path("var/exports"),
) -> None:
    """Register both product flights for the current session."""
    st.session_state[_RUNNERS_KEY] = {
        FlightKind.SECURITY.value: security,
        FlightKind.TRANSVERSAL.value: transversal,
    }
    st.session_state[_EXPORT_ROOT_KEY] = export_root


def current_flight_runner(kind: FlightKind) -> Callable[[], FlightReport]:
    """Return the registered runner or a deterministic in-memory fallback."""
    runners = st.session_state.get(_RUNNERS_KEY)
    runner = runners.get(kind.value) if isinstance(runners, dict) else None
    if callable(runner):
        return cast(Callable[[], FlightReport], runner)
    profile = st.session_state.get(_PROFILE_KEY)
    configuration = profile if isinstance(profile, FlightConfiguration) else None
    if kind is FlightKind.SECURITY:
        return lambda: run_security_flight(configuration)
    return lambda: run_transversal_memory_flight(configuration)


def run_assurance_demo(
    kind: FlightKind,
    runner: Callable[[], FlightReport],
) -> None:
    """Run one product validation and persist its complete audit package."""
    report = runner()
    if report.flight_kind is not kind:
        raise ValueError("flight runner returned a report for a different product scope")
    reports = dict(st.session_state.get(_REPORTS_KEY, {}))
    reports[kind.value] = report
    st.session_state[_REPORTS_KEY] = reports
    generated = build_flight_exports(report)
    exports = dict(st.session_state.get(_EXPORTS_KEY, {}))
    exports[kind.value] = generated
    st.session_state[_EXPORTS_KEY] = exports
    export_root = st.session_state.get(_EXPORT_ROOT_KEY, Path("var/exports"))
    if not isinstance(export_root, Path):
        raise TypeError("session export root must be a Path")
    persisted = dict(st.session_state.get(_PERSISTED_RUNS_KEY, {}))
    persisted[kind.value] = persist_flight_run(export_root, report, generated)
    st.session_state[_PERSISTED_RUNS_KEY] = persisted
    st.session_state[_ACTIVE_KIND_KEY] = kind.value


def current_report(kind: FlightKind | None = None) -> FlightReport | None:
    """Return the current report when the session contains a valid result."""
    reports = st.session_state.get(_REPORTS_KEY)
    if not isinstance(reports, dict):
        return None
    selected = kind.value if kind is not None else st.session_state.get(_ACTIVE_KIND_KEY)
    report = reports.get(selected) if isinstance(selected, str) else None
    return report if isinstance(report, FlightReport) else None


def current_exports(report: FlightReport) -> FlightExports:
    """Return cached exports or build them from the current report."""
    cached = st.session_state.get(_EXPORTS_KEY)
    if isinstance(cached, dict):
        exports = cached.get(report.flight_kind.value)
        if isinstance(exports, FlightExports):
            return exports
    else:
        cached = {}
    exports = build_flight_exports(report)
    cached[report.flight_kind.value] = exports
    st.session_state[_EXPORTS_KEY] = cached
    return exports


def current_persisted_run(report: FlightReport) -> PersistedFlightRun | None:
    """Return local persistence details for a completed run."""
    persisted = st.session_state.get(_PERSISTED_RUNS_KEY)
    if not isinstance(persisted, dict):
        return None
    value = persisted.get(report.flight_kind.value)
    return value if isinstance(value, PersistedFlightRun) else None
