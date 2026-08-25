"""Session-level operational profile page."""

from html import escape

import streamlit as st

from sodif.demo.models import FlightConfiguration
from sodif.settings import AppSettings
from sodif.ui.pages.shared import render_page_intro
from sodif.ui.state import (
    initialize_operational_profile,
    reset_operational_profile,
    save_operational_profile,
)


def render_configuration(settings: AppSettings) -> None:
    """Edit validated operational values retained for the active session."""
    profile = initialize_operational_profile(settings)
    render_page_intro(
        "Administrare produs",
        "Configurare operațională",
        "Definește contextul utilizat de rulări, politicile Gateway și rapoartele generate. "
        "Valorile sunt validate și păstrate pe durata sesiunii curente.",
    )
    _render_active_profile(profile)
    with st.form("operational_profile_form", border=True):
        identity, transaction = st.columns(2, gap="large")
        with identity:
            st.markdown("#### Context organizațional")
            organization = st.text_input("Organizație", value=profile.organization_name)
            workspace = st.text_input("Spațiu operațional", value=profile.workspace_name)
            domain = st.text_input("Domeniu", value=profile.domain_name)
            environment = st.text_input("Mediu", value=profile.environment)
        with transaction:
            st.markdown("#### Limită API protejată")
            protected_service = st.text_input(
                "Serviciu protejat",
                value=profile.protected_service,
            )
            route_id = st.text_input("Politică de rutare", value=profile.route_id)
            audience = st.text_input("Audiență autorizată", value=profile.audience)
            path_prefix = st.text_input("Resursă API", value=profile.path_prefix)
            maximum_parameters = st.number_input(
                "Limită parametri",
                min_value=1,
                max_value=256,
                value=profile.maximum_parameters,
                step=1,
            )
        submitted = st.form_submit_button(
            "Salvează configurația",
            type="primary",
            icon=":material/save:",
            use_container_width=True,
        )
    if submitted:
        save_operational_profile(
            FlightConfiguration(
                session_id=profile.session_id,
                organization_name=organization,
                workspace_name=workspace,
                domain_name=domain,
                environment=environment,
                protected_service=protected_service,
                route_id=route_id,
                audience=audience,
                path_prefix=path_prefix,
                maximum_parameters=int(maximum_parameters),
            )
        )
        st.rerun()

    if st.button(
        "Revino la valorile preconfigurate",
        icon=":material/restart_alt:",
    ):
        reset_operational_profile(settings)
        st.rerun()


def _render_active_profile(profile: FlightConfiguration) -> None:
    st.markdown(
        f"""
        <section class="sodif-report-identity">
            <div><small>Organizație</small><strong>{escape(profile.organization_name)}</strong></div>
            <div><small>Domeniu</small><strong>{escape(profile.domain_name)}</strong></div>
            <div><small>Serviciu</small><strong>{escape(profile.protected_service)}</strong></div>
            <div><small>Rută activă</small><code>{escape(profile.route_id)}</code></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
