"""SODIF platform architecture page."""

from html import escape

import streamlit as st

from sodif.product import MODULES
from sodif.settings import AppSettings
from sodif.ui.pages.shared import render_page_intro


def render_product_explainer(settings: AppSettings) -> None:
    """Explain product boundaries and the end-to-end trust chain."""
    render_page_intro(
        "Arhitectura produsului",
        "Arhitectură modulară și lanț verificabil de execuție",
        "SODIF Security, SODIF Archive și SODIF Gateway au responsabilități precise și "
        "schimbă între ele artefacte criptografice verificabile.",
    )

    active_modules = [module for module in MODULES if settings.modules.is_enabled(module.key)]
    columns = st.columns(len(active_modules)) if active_modules else ()
    for column, module in zip(columns, active_modules, strict=True):
        with column:
            st.markdown(
                f"""
                <article class="sodif-architecture-card module-{escape(module.key)}">
                    <small>{escape(module.sequence)} · {escape(module.navigation_label)}</small>
                    <h2>{escape(module.name)}</h2>
                    <p>{escape(module.responsibility)}</p>
                    <footer><b>Produce</b><span>{escape(module.output_contract)}</span></footer>
                </article>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="sodif-section-label">Lanțul transversal</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <section class="sodif-platform-flow">
            <div><small>Sursă</small><strong>Revizie semnată</strong></div><i></i>
            <div><small>Înțelegere</small><strong>Consens + intenție</strong></div><i></i>
            <div><small>Autorizare</small><strong>Permis + Gateway</strong></div><i></i>
            <div><small>Efect</small><strong>Acțiune API controlată</strong></div>
        </section>
        <p class="sodif-inline-note">SODIF Archive și registrul criptografic păstrează
        proveniența, deciziile și artefactele de audit pe întregul traseu.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sodif-section-label">Contracte și extensibilitate</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            <article class="sodif-feature-panel">
                <div class="sodif-card-caption">Contracte stabile</div>
                <h2>Contractele dintre module sunt verificabile.</h2>
                <p>Permisul, amprentele documentelor și deciziile de enforcement au forme
                explicite, versionabile și verificabile independent.</p>
            </article>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <article class="sodif-feature-panel accent">
                <div class="sodif-card-caption">Extensibilitate controlată</div>
                <h2>Pachetele de domeniu extind aceeași arhitectură.</h2>
                <p>Schemele de intenție, regulile de risc și adaptoarele API pot fi extinse
                separat, păstrând aceleași garanții criptografice și de audit.</p>
            </article>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <section class="sodif-boundary-panel">
            <div><div class="sodif-section-label light">Poziționare</div>
            <h2>Între aprobarea formală și sistemul care produce efectul.</h2></div>
            <p>SODIF completează semnătura electronică, identitatea și politicile clasice
            ale gateway-ului cu un control explicit asupra tranzacției autorizate.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
