"""Product explanation and differentiation page."""

import streamlit as st

from sodif.ui.pages.shared import render_page_intro


def render_product_explainer(control_page: str) -> None:
    """Explain the product flow without exposing implementation vocabulary."""
    render_page_intro(
        "Model de control",
        "Cum funcționează SODIF",
        "Un strat de siguranță care transformă aprobarea din document într-o autorizație "
        "digitală precisă, verificabilă și de unică folosință.",
    )

    st.markdown(
        '<div class="sodif-section-label compact">De la aprobare la execuție</div>',
        unsafe_allow_html=True,
    )
    steps = (
        (
            "verified_user",
            "Verifică documentul",
            "Confirmă semnătura, revizia și integritatea înaintea oricărei interpretări.",
        ),
        (
            "compare_arrows",
            "Confirmă intenția",
            "Confruntă independent valorile care pot schimba efectul tranzacției.",
        ),
        (
            "policy",
            "Aplică verificarea potrivită",
            "Extinde controlul numai când dovezile inițiale sunt insuficiente sau divergente.",
        ),
        (
            "key",
            "Emite permisul unic",
            "Leagă rezultatul de metoda, ruta, parametrii și destinația API aprobate.",
        ),
        (
            "shield_lock",
            "Protejează execuția",
            "Respinge modificarea acțiunii și orice tentativă de reutilizare a permisului.",
        ),
    )
    columns = st.columns(5)
    for column, (icon, title, body) in zip(columns, steps, strict=True):
        with column, st.container(border=True, key=f"product_step_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)

    st.markdown(
        '<div class="sodif-section-label">Diferențiere practică</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            <article class="sodif-feature-panel">
                <div class="sodif-card-caption">Control semantic aplicat</div>
                <h2>Decizia privește tranzacția, nu doar identitatea apelantului.</h2>
                <p>SODIF verifică dacă acțiunea digitală păstrează valorile și limitele
                aprobate în document, chiar dacă apelantul este autorizat, iar API-ul
                este legitim.</p>
            </article>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <article class="sodif-feature-panel accent">
                <div class="sodif-card-caption">Eficiență adaptivă</div>
                <h2>Consumă dovezi suplimentare numai când decizia o cere.</h2>
                <p>Fluxul conform se încheie rapid. Situațiile incomplete sau riscante
                primesc verificări suplimentare și se opresc controlat dacă rămân ambigue.</p>
            </article>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <section class="sodif-boundary-panel">
            <div><div class="sodif-section-label light">Poziționare în arhitectură</div>
            <h2>Înaintea sistemului care produce efectul.</h2></div>
            <p>SODIF poate proteja direct un API sau poate funcționa împreună cu un gateway,
            fără să înlocuiască autentificarea, semnătura electronică ori arhivarea.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="product_demo_link"):
        st.page_link(
            control_page,
            label="Vezi controalele în acțiune",
            icon=":material/play_arrow:",
            use_container_width=False,
        )
