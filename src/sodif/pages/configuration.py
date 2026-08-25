"""Streamlit entry point for operational configuration."""

from sodif.settings import load_settings
from sodif.ui.pages.configuration import render_configuration

render_configuration(load_settings())
