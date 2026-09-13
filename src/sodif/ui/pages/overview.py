"""Marketing-oriented product overview."""

from html import escape

import streamlit as st

from sodif.product import MODULES
from sodif.settings import AppSettings


def render_overview(settings: AppSettings, architecture_page: str) -> None:
    """Render the platform promise, product modules, and immediate use cases."""
    st.markdown(
        """
        <section class="sodif-hero">
            <div class="sodif-eyebrow">PLATFORMĂ DE SECURITATE CIBERNETICĂ</div>
            <h1>Control verificabil de la aprobarea semnată la execuția API.</h1>
            <p class="sodif-lead">SODIF protejează continuitatea dintre revizia semnată,
            intenția operațională, permisul criptografic și cererea executată de sistemul
            destinație.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    cta, promise = st.columns((0.31, 0.69), vertical_alignment="center")
    with cta, st.container(key="overview_architecture_link"):
        st.page_link(
            architecture_page,
            label="Explorează platforma",
            icon=":material/arrow_forward:",
            use_container_width=True,
        )
    with promise:
        st.markdown(
            f'<p class="sodif-promise">{escape(settings.tagline)}</p>',
            unsafe_allow_html=True,
        )

    enabled_modules = [module for module in MODULES if settings.modules.is_enabled(module.key)]
    if enabled_modules:
        st.markdown(
            '<div class="sodif-section-label">Platforma SODIF</div>',
            unsafe_allow_html=True,
        )
        columns = st.columns(len(enabled_modules))
        for column, module in zip(columns, enabled_modules, strict=True):
            with column:
                st.markdown(
                    f"""
                    <article class="sodif-module-card module-{escape(module.key)}">
                        <div class="sodif-module-card-head"><span>{escape(module.sequence)}</span>
                        <small>Modul de produs</small></div>
                        <h2>{escape(module.name)}</h2>
                        <p>{escape(module.promise)}</p>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
                st.page_link(
                    module.page,
                    label=module.navigation_label,
                    icon=module.icon,
                    use_container_width=True,
                )

    st.markdown(
        """
        <section class="sodif-value-panel">
            <div>
                <div class="sodif-section-label light">Control aplicat tranzacției</div>
                <h2>API-ul execută exact intenția aprobată.</h2>
                <p>Identitatea, integritatea, semnificația operațională și efectul digital
                rămân legate prin artefacte verificabile pe întregul traseu.</p>
            </div>
            <div class="sodif-protection-list">
                <div><span></span><p><b>Verifică</b>
                <small>Document, semnătură și valori cu efect critic</small></p></div>
                <div><span></span><p><b>Păstrează</b>
                <small>Revizii, audit și istoric criptografic</small></p></div>
                <div><span></span><p><b>Execută</b>
                <small>Doar acțiunea API autorizată, o singură dată</small></p></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sodif-section-label">Aplicabilitate imediată</div>',
        unsafe_allow_html=True,
    )
    use_cases = st.columns(3)
    cases = (
        ("Achiziții", "Comenzile semnate devin cereri ERP controlate și trasabile."),
        ("Operațiuni reglementate", "Aprobările formale autorizează numai efectul prevăzut."),
        (
            "Integrare între organizații",
            "Documentele semnate coordonează API-uri fără încredere implicită.",
        ),
    )
    for column, (title, body) in zip(use_cases, cases, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-use-card"><h3>{escape(title)}</h3>'
                f"<p>{escape(body)}</p></article>",
                unsafe_allow_html=True,
            )
