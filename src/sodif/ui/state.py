"""Session-scoped product state shared by Streamlit pages."""

from collections.abc import Callable
from typing import cast

import streamlit as st

from sodif.demo.models import FlightKind, FlightReport
from sodif.demo.runner import run_security_flight, run_transversal_memory_flight
from sodif.reporting import FlightExports, build_flight_exports

_REPORTS_KEY = "sodif_flight_reports"
_EXPORTS_KEY = "sodif_flight_exports"
_RUNNERS_KEY = "sodif_flight_runners"
_ACTIVE_KIND_KEY = "sodif_active_flight_kind"


def register_flight_runners(
    security: Callable[[], FlightReport],
    transversal: Callable[[], FlightReport],
) -> None:
    """Register both product flights for the current session."""
    st.session_state[_RUNNERS_KEY] = {
        FlightKind.SECURITY.value: security,
        FlightKind.TRANSVERSAL.value: transversal,
    }


def current_flight_runner(kind: FlightKind) -> Callable[[], FlightReport]:
    """Return the registered runner or a deterministic in-memory fallback."""
    runners = st.session_state.get(_RUNNERS_KEY)
    runner = runners.get(kind.value) if isinstance(runners, dict) else None
    if callable(runner):
        return cast(Callable[[], FlightReport], runner)
    return run_security_flight if kind is FlightKind.SECURITY else run_transversal_memory_flight


def run_assurance_demo(
    kind: FlightKind,
    runner: Callable[[], FlightReport],
) -> None:
    """Run the deterministic demonstration and retain its evidence."""
    report = runner()
    if report.flight_kind is not kind:
        raise ValueError("flight runner returned a report for a different product scope")
    reports = dict(st.session_state.get(_REPORTS_KEY, {}))
    reports[kind.value] = report
    st.session_state[_REPORTS_KEY] = reports
    exports = dict(st.session_state.get(_EXPORTS_KEY, {}))
    exports[kind.value] = build_flight_exports(report)
    st.session_state[_EXPORTS_KEY] = exports
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
