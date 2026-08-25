"""Streamlit entry point for the product explanation."""

from sodif.settings import load_settings
from sodif.ui.pages.product import render_product_explainer

render_product_explainer(load_settings())
