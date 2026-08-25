"""Semantic Execution Gateway product module page."""

import streamlit as st

from sodif.product import product_module
from sodif.ui.pages.shared import render_module_contract, render_module_intro


def render_gateway_module() -> None:
    """Present the gateway enforcement boundary and policy model."""
    module = product_module("gateway")
    render_module_intro(module)
    render_module_contract(module)

    st.markdown(
        '<div class="sodif-section-label compact">Politici aplicate tranzacției</div>',
        unsafe_allow_html=True,
    )
    policies = (
        (
            "route",
            "Potrivire exactă",
            "Metoda, ruta și parametrii cererii trebuie să coincidă cu acțiunea autorizată.",
        ),
        (
            "domain_verification",
            "Destinație controlată",
            "Permisul este acceptat numai de serviciul și mediul pentru care a fost emis.",
        ),
        (
            "timer",
            "Fereastră limitată",
            "Expirarea și consumul unic reduc suprafața de abuz a unei aprobări valide.",
        ),
        (
            "policy_alert",
            "Blocare motivată",
            "Orice abatere produce o decizie explicită și o urmă de audit "
            "fără efect asupra API-ului.",
        ),
    )
    columns = st.columns(4)
    for column, (icon, title, body) in zip(columns, policies, strict=True):
        with column, st.container(border=True, key=f"gateway_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)

    st.markdown(
        """
        <section class="sodif-gateway-flow">
            <div><small>Cerere</small><strong>API call + permis</strong>
            <span>Tranzacția pregătită pentru execuție</span></div>
            <i aria-hidden="true"></i>
            <div class="active"><small>Enforcement</small>
            <strong>Semantic Execution Gateway</strong>
            <span>Identitate, intenție, destinație și unicitate</span></div>
            <i aria-hidden="true"></i>
            <div><small>Rezultat</small><strong>Route / Block</strong>
            <span>O singură decizie, justificată și auditabilă</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="sodif-boundary-panel">
            <div><div class="sodif-section-label light">Integrare pragmatică</div>
            <h2>Un punct de control, fără rescrierea API-urilor protejate.</h2></div>
            <p>Gateway-ul păstrează funcțiile clasice de rutare și politici tehnice, iar SODIF
            adaugă verificarea dreptului tranzacțional derivat din documentul semnat.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
