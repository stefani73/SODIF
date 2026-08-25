"""Semantic Execution Gateway module entry point."""

from sodif.settings import load_settings
from sodif.ui.pages.gateway import render_gateway_module

render_gateway_module(load_settings().gateway)
