"""Multipage product shell for the SODIF Streamlit experience."""

from collections.abc import Callable
from functools import partial
from html import escape

import streamlit as st

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_integrated_flight, run_security_flight
from sodif.settings import AppSettings
from sodif.ui.state import register_flight_runners
from sodif.ui.styles import PRODUCT_STYLES


def configure_page(settings: AppSettings) -> None:
    """Apply browser metadata before rendering any UI element."""
    st.set_page_config(
        page_title=f"{settings.app_name} | Controlul intenției semnate",
        page_icon=":material/shield_lock:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={},
    )


def render_product_shell(
    settings: AppSettings,
    flight_runner: Callable[[], FlightReport] | None = None,
) -> None:
    """Render the product navigation and execute the selected page."""
    st.markdown(PRODUCT_STYLES, unsafe_allow_html=True)
    integrated_runner = flight_runner or partial(run_integrated_flight, settings.archive_root)
    register_flight_runners(run_security_flight, integrated_runner)
    _render_sidebar_brand(settings)

    overview_page = st.Page(
        "pages/overview.py",
        title="Prezentare",
        icon=":material/home:",
        url_path="overview",
        default=True,
    )
    product_page = st.Page(
        "pages/product.py",
        title="Cum funcționează",
        icon=":material/account_tree:",
        url_path="product",
    )
    ingestion_page = st.Page(
        "pages/ingestion.py",
        title="Preluare documente",
        icon=":material/upload_file:",
        url_path="ingestion",
    )
    registry_page = st.Page(
        "pages/registry.py",
        title="Registru documente",
        icon=":material/folder_open:",
        url_path="registry",
    )
    control_page = st.Page(
        "pages/control.py",
        title="Centru de control",
        icon=":material/shield_lock:",
        url_path="control",
    )
    reports_page = st.Page(
        "pages/reports.py",
        title="Rapoarte și dovezi",
        icon=":material/fact_check:",
        url_path="reports",
    )
    navigation = st.navigation(
        {
            "Produs": (overview_page, product_page),
            "Documente": (ingestion_page, registry_page),
            "Demonstrație": (control_page, reports_page),
        },
        position="sidebar",
        expanded=True,
    )
    _render_sidebar_footer()
    _render_header(settings)
    navigation.run()


def _render_sidebar_brand(settings: AppSettings) -> None:
    name = escape(settings.app_name)
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sodif-sidebar-brand">
                <span class="sodif-mark" aria-hidden="true"><i></i></span>
                <div><strong>{name}</strong><small>Controlul intenției semnate</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_sidebar_footer() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sodif-sidebar-footer">
                <span></span><div><strong>Sistem disponibil</strong>
                <small>Serviciul de verificare este pregătit.</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_header(settings: AppSettings) -> None:
    name = escape(settings.app_name)
    st.markdown(
        f"""
        <div class="sodif-header">
            <div class="sodif-brand">
                <span class="sodif-wordmark">{name}</span>
                <span class="sodif-context">Controlul intenției semnate</span>
            </div>
            <div class="sodif-trust-chip"><span></span> Execuție protejată</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
