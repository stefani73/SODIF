"""Minimal, product-oriented Streamlit shell used by the foundation step."""

import streamlit as st

from sodif.settings import AppSettings


def configure_page(settings: AppSettings) -> None:
    """Apply stable browser metadata before rendering UI elements."""
    st.set_page_config(
        page_title=f"{settings.app_name} — Signed Intent Execution",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def render_foundation_shell(settings: AppSettings) -> None:
    """Render the verified Step 1 shell without functional SODIF behavior."""
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(135deg, #ffffff 0%, #f5f8fb 100%); }
        .block-container { max-width: 1180px; padding-top: 5rem; }
        [data-testid="stHeader"] { background: transparent; }
        .sodif-eyebrow {
            color: #0b8793; font-size: .78rem; font-weight: 750;
            letter-spacing: .14em; text-transform: uppercase; margin-bottom: .5rem;
        }
        .sodif-subtitle { color: #52657b; font-size: 1.1rem; max-width: 760px; }
        .sodif-card {
            background: rgba(255,255,255,.9); border: 1px solid #dbe4ec;
            border-radius: 14px; padding: 1.1rem 1.25rem; min-height: 112px;
            box-shadow: 0 8px 30px rgba(16,35,63,.05);
        }
        .sodif-label { color: #64748b; font-size: .75rem; text-transform: uppercase; }
        .sodif-value { color: #10233f; font-size: 1.05rem; font-weight: 700; margin-top: .4rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sodif-eyebrow">Signed Intent Execution</div>', unsafe_allow_html=True)
    st.title(settings.app_name)
    st.markdown(f"### {settings.tagline}")
    st.markdown(
        '<p class="sodif-subtitle">Control verificabil între documentul semnat și acțiunea '
        "digitală executată.</p>",
        unsafe_allow_html=True,
    )

    columns = st.columns(3)
    cards = (
        ("Livrare", "Pasul 5 · Execution Permit"),
        ("Calitate", "Porți automate active"),
        ("Mediu", settings.environment.capitalize()),
    )
    for column, (label, value) in zip(columns, cards, strict=True):
        with column:
            st.markdown(
                f'<div class="sodif-card"><div class="sodif-label">{label}</div>'
                f'<div class="sodif-value">{value}</div></div>',
                unsafe_allow_html=True,
            )

    st.info(
        "Consensul acceptat este transformat într-un permis criptografic scurt, legat de "
        "acțiunea API exactă și consumabil o singură dată."
    )
    st.caption(f"Release {settings.release} · Python OSS · local-first")
