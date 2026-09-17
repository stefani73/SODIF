"""SODIF Security product module page."""

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
            "Invariabilitate semantică",
            "Compară structura PDF cu două trasee vizuale distincte, randate prin MuPDF "
            "și Poppler și citite cu Tesseract, apoi fixează proveniența fiecărui câmp critic.",
        ),
        (
            "key_vertical",
            "Permis legat de execuție",
            "Leagă rădăcina valorilor aprobate de metodă, rută, parametri, destinație "
            "și termen într-un permis unic.",
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
            <h2>Aceleași valori trebuie să rămână stabile până la execuția API.</h2>
            <p>Profilurile de extragere sunt selectate după validarea semnăturii. Traseele
            vizuale folosesc același motor OCR în configurații diferite; independența completă
            între motoare rămâne o etapă de dezvoltare. Valorile critice confirmate sunt
            angajate criptografic, iar gateway-ul verifică legătura fiecărui parametru cu
            documentul înainte de rutare.</p></div>
            <div class="sodif-protection-list">
                <div><span></span><p><b>Pragmatism</b>
                <small>Traseu scurt pentru cazurile coerente,
                extindere numai la nevoie</small></p></div>
                <div><span></span><p><b>Siguranță</b>
                <small>Blocare când structura PDF și forma vizibilă nu coincid</small></p></div>
                <div><span></span><p><b>Trasabilitate</b>
                <small>Proveniență pe câmp, rădăcină criptografică
                și dovadă de execuție</small></p></div>
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
