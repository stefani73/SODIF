"""Multipage product shell for the SODIF Streamlit experience."""

from collections.abc import Callable
from functools import partial
from html import escape

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_security_flight, run_transversal_flight
from sodif.settings import AppSettings
from sodif.ui.state import initialize_operational_profile, register_flight_runners
from sodif.ui.styles import PRODUCT_STYLES


def configure_page(settings: AppSettings) -> None:
    """Apply browser metadata before rendering any UI element."""
    st.set_page_config(
        page_title=f"{settings.app_name} | Signed Intent Control",
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
    profile = initialize_operational_profile(settings)
    security_runner = partial(run_security_flight, profile)
    transversal_runner = flight_runner or partial(
        run_transversal_flight,
        settings.archive_root,
        profile,
    )
    register_flight_runners(security_runner, transversal_runner, settings.export_root)
    _render_sidebar_brand(settings)

    overview_page = st.Page(
        "pages/overview.py",
        title="Prezentare",
        icon=":material/home:",
        url_path="overview",
        default=True,
    )
    architecture_page = st.Page(
        "pages/product.py",
        title="Arhitectura platformei",
        icon=":material/account_tree:",
        url_path="product",
    )
    configuration_page = st.Page(
        "pages/configuration.py",
        title="Configurare operațională",
        icon=":material/tune:",
        url_path="configuration",
    )
    security_page = st.Page(
        "pages/security.py",
        title="Signed Intent Security",
        icon=":material/shield_lock:",
        url_path="security",
    )
    archive_page = st.Page(
        "pages/archive.py",
        title="Verifiable Document Archive",
        icon=":material/folder_managed:",
        url_path="archive",
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
    gateway_page = st.Page(
        "pages/gateway.py",
        title="Semantic Execution Gateway",
        icon=":material/hub:",
        url_path="gateway",
    )
    control_page = st.Page(
        "pages/control.py",
        title="Centru de control",
        icon=":material/shield_lock:",
        url_path="control",
    )
    reports_page = st.Page(
        "pages/reports.py",
        title="Audit și exporturi",
        icon=":material/fact_check:",
        url_path="reports",
    )
    sections: dict[str, tuple[StreamlitPage, ...]] = {
        "Platformă": (overview_page, architecture_page, configuration_page)
    }
    if settings.modules.security_enabled:
        sections["Signed Intent Security"] = (security_page,)
    if settings.modules.archive_enabled:
        sections["Verifiable Document Archive"] = (
            archive_page,
            ingestion_page,
            registry_page,
        )
    if settings.modules.gateway_enabled:
        sections["Semantic Execution Gateway"] = (gateway_page,)
    if settings.modules.security_enabled:
        sections["Operațiuni și audit"] = (control_page, reports_page)

    navigation = st.navigation(sections, position="sidebar", expanded=True)
    _render_sidebar_footer(profile.environment)
    _render_header(settings, profile.organization_name, profile.domain_name)
    navigation.run()


def _render_sidebar_brand(settings: AppSettings) -> None:
    name = escape(settings.app_name)
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sodif-sidebar-brand">
                <span class="sodif-mark" aria-hidden="true"><i></i></span>
                <div><strong>{name}</strong><small>Signed Intent Infrastructure</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_sidebar_footer(environment: str) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sodif-sidebar-footer">
                <span></span><div><strong>Politici active</strong>
                <small>Mediu: {escape(environment)}</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_header(settings: AppSettings, organization: str, domain: str) -> None:
    name = escape(settings.app_name)
    st.markdown(
        f"""
        <div class="sodif-header">
            <div class="sodif-brand">
                <span class="sodif-wordmark">{name}</span>
                <span class="sodif-context">{escape(organization)} · {escape(domain)}</span>
            </div>
            <div class="sodif-trust-chip"><span></span> Lanț de încredere activ</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
