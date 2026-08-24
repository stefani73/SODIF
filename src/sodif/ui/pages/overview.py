"""Marketing-oriented product overview."""

from html import escape

import streamlit as st

from sodif.settings import AppSettings


def render_overview(settings: AppSettings, control_page: str) -> None:
    """Render the product promise, value chain, and immediate use cases."""
    st.markdown(
        """
        <section class="sodif-hero">
            <div class="sodif-eyebrow">Încredere verificabilă între document și API</div>
            <h1>Din document semnat în acțiune digitală de încredere.</h1>
            <p class="sodif-lead">SODIF verifică intenția aprobată, o leagă criptografic
            de acțiunea API exactă și împiedică modificarea sau repetarea execuției.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    cta, promise = st.columns((0.31, 0.69), vertical_alignment="center")
    with cta, st.container(key="overview_demo_link"):
        st.page_link(
            control_page,
            label="Deschide demonstrația",
            icon=":material/play_arrow:",
            use_container_width=True,
        )
    with promise:
        st.markdown(
            f'<p class="sodif-promise">{escape(settings.tagline)}</p>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sodif-section-label">Lanțul de încredere</div>', unsafe_allow_html=True
    )
    columns = st.columns(4)
    chain = (
        ("Document autentic", "Semnătura și revizia sunt verificate înainte de interpretare."),
        ("Intenție confirmată", "Valorile critice sunt confruntate între dovezi independente."),
        ("Permis unic", "Aprobarea este legată de acțiunea API și de destinația exactă."),
        ("Execuție controlată", "Orice modificare sau reutilizare este oprită înainte de API."),
    )
    for column, (title, body) in zip(columns, chain, strict=True):
        with column:
            st.markdown(
                f"""
                <article class="sodif-chain-card">
                    <div class="sodif-card-signal"><span></span></div>
                    <h3>{escape(title)}</h3><p>{escape(body)}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <section class="sodif-value-panel">
            <div>
                <div class="sodif-section-label light">Control aplicat tranzacției</div>
                <h2>API-ul execută intenția aprobată, nu o aproximare.</h2>
                <p>Politicile clasice decid cine poate apela un API. SODIF verifică și dacă
                acțiunea cerută păstrează exact sensul documentului semnat.</p>
            </div>
            <div class="sodif-protection-list">
                <div><span></span><p><b>Integritate</b>
                <small>Oprește documentele modificate după semnare</small></p></div>
                <div><span></span><p><b>Claritate</b>
                <small>Semnalează valorile critice aflate în conflict</small></p></div>
                <div><span></span><p><b>Precizie</b>
                <small>Respinge parametrii API diferiți de cei autorizați</small></p></div>
                <div><span></span><p><b>Unicitate</b>
                <small>Împiedică reutilizarea aceleiași autorizări</small></p></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sodif-section-label">Aplicabilitate imediată</div>', unsafe_allow_html=True
    )
    use_cases = st.columns(3)
    cases = (
        ("Achiziții", "Comenzile semnate devin cereri ERP controlate și trasabile."),
        ("Operațiuni reglementate", "Aprobările formale autorizează numai acțiunea prevăzută."),
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
