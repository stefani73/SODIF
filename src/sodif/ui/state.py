"""Session-scoped product state shared by Streamlit pages."""

from collections.abc import Callable

import streamlit as st

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_default_flight
from sodif.reporting import FlightExports, build_flight_exports

_REPORT_KEY = "sodif_flight_report"
_EXPORTS_KEY = "sodif_flight_exports"
_RUNNER_KEY = "sodif_flight_runner"


def register_flight_runner(runner: Callable[[], FlightReport]) -> None:
    """Register the runner used by the control page in the current session."""
    st.session_state[_RUNNER_KEY] = runner


def current_flight_runner() -> Callable[[], FlightReport]:
    """Return the registered runner or the deterministic default."""
    runner = st.session_state.get(_RUNNER_KEY)
    return runner if callable(runner) else run_default_flight


def run_assurance_demo(runner: Callable[[], FlightReport]) -> None:
    """Run the deterministic demonstration and retain its evidence."""
    report = runner()
    st.session_state[_REPORT_KEY] = report
    st.session_state[_EXPORTS_KEY] = build_flight_exports(report)


def current_report() -> FlightReport | None:
    """Return the current report when the session contains a valid result."""
    report = st.session_state.get(_REPORT_KEY)
    return report if isinstance(report, FlightReport) else None


def current_exports(report: FlightReport) -> FlightExports:
    """Return cached exports or build them from the current report."""
    exports = st.session_state.get(_EXPORTS_KEY)
    if isinstance(exports, FlightExports):
        return exports
    exports = build_flight_exports(report)
    st.session_state[_EXPORTS_KEY] = exports
    return exports
