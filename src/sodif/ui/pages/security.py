"""Signed Intent Security product module page."""

import streamlit as st

from sodif.product import product_module
from sodif.ui.pages.shared import render_module_contract, render_module_intro


def render_security_module(control_page: str) -> None:
    """Present the signature-to-permit security boundary."""
    module = product_module("security")
    render_module_intro(module)
    render_module_contract(module)

    st.markdown(
        '<div class="sodif-section-label compact">Controale esențiale</div>',
        unsafe_allow_html=True,
    )
    controls = (
        (
            "verified_user",
            "Încredere în document",
            "Verifică integritatea, semnătura și continuitatea reviziei înainte de interpretare.",
        ),
        (
            "neurology",
            "Consens semantic adaptiv",
            "Confruntă independent valorile cu efect tranzacțional și extinde analiza "
            "numai la risc.",
        ),
        (
            "key_vertical",
            "Permis legat de execuție",
            "Fixează metoda, ruta, parametrii, destinația și termenul autorizării "
            "într-un permis unic.",
        ),
        (
            "replay",
            "Protecție anti-replay",
            "Oprește reutilizarea aprobării chiar dacă documentul și apelantul rămân legitime.",
        ),
    )
    columns = st.columns(4)
    for column, (icon, title, body) in zip(columns, controls, strict=True):
        with column, st.container(border=True, key=f"security_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)

    st.markdown(
        """
        <section class="sodif-value-panel sodif-module-value">
            <div><div class="sodif-section-label light">Decizie explicabilă</div>
            <h2>Controlul crește numai când tranzacția o cere.</h2>
            <p>Cazurile coerente folosesc traseul scurt. Valorile divergente, lipsa confirmărilor
            sau abaterea acțiunii API declanșează verificări suplimentare ori blocarea.</p></div>
            <div class="sodif-protection-list">
                <div><span></span><p><b>Pragmatism</b>
                <small>Fără procesare redundantă pentru tranzacțiile clare</small></p></div>
                <div><span></span><p><b>Siguranță</b>
                <small>Fail-closed când sensul critic nu poate fi confirmat</small></p></div>
                <div><span></span><p><b>Trasabilitate</b>
                <small>Motiv și trasabilitate pentru fiecare decizie</small></p></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="security_demo_link"):
        st.page_link(
            control_page,
            label="Deschide Security Flight",
            icon=":material/play_arrow:",
            use_container_width=False,
        )
