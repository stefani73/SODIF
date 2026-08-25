"""Streamlit entry point for the control center."""

from sodif.demo.models import FlightKind
from sodif.ui.pages.control import render_control_center
from sodif.ui.state import current_flight_runner

render_control_center(
    current_flight_runner(FlightKind.SECURITY),
    current_flight_runner(FlightKind.INTEGRATED),
    "pages/reports.py",
    "pages/registry.py",
)
