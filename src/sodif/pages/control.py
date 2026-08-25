"""Streamlit entry point for the control center."""

from sodif.ui.pages.control import render_control_center
from sodif.ui.state import current_flight_runner

render_control_center(
    current_flight_runner(),
    "pages/reports.py",
    "pages/registry.py",
)
