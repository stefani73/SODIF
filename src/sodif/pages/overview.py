"""Streamlit entry point for the product overview."""

from sodif.settings import load_settings
from sodif.ui.pages.overview import render_overview

render_overview(load_settings(), "pages/control.py")
