"""Shared presentation components for product pages."""

from html import escape

import streamlit as st

from sodif.ui.presentation import FlightView


def render_page_intro(eyebrow: str, title: str, lead: str) -> None:
    """Render a consistent page introduction."""
    st.markdown(
        f"""
        <section class="sodif-page-intro">
            <div class="sodif-eyebrow">{escape(eyebrow)}</div>
            <h1 class="sodif-page-title">{escape(title)}</h1>
            <p class="sodif-page-lead">{escape(lead)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_flight_summary(view: FlightView) -> None:
    """Render the user-facing conclusion of a completed demonstration."""
    st.markdown(
        f"""
        <section class="sodif-flight-summary {view.tone}">
            <span class="sodif-summary-icon" aria-hidden="true"></span>
            <div><div class="sodif-summary-kicker">Rezultatul demonstrației</div>
            <h2>{escape(view.title)}</h2><p>{escape(view.detail)}</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
