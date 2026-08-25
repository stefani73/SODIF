"""Verifiable Document Archive product module page."""

import streamlit as st

from sodif.product import product_module
from sodif.ui.pages.shared import render_module_contract, render_module_intro


def render_archive_module(ingestion_page: str, registry_page: str) -> None:
    """Present the archive boundary and its focused workspaces."""
    module = product_module("archive")
    render_module_intro(module)
    render_module_contract(module)

    st.markdown(
        '<div class="sodif-section-label compact">Spații de lucru</div>',
        unsafe_allow_html=True,
    )
    intake, registry = st.columns(2)
    with intake, st.container(border=True, key="archive_intake_workspace"):
        st.markdown("#### :material/upload_file: Preluare controlată")
        st.caption(
            "Validează documentul și dovada de semnătură înainte ca revizia să intre în arhivă."
        )
        st.page_link(
            ingestion_page,
            label="Deschide preluarea",
            icon=":material/arrow_forward:",
        )
    with registry, st.container(border=True, key="archive_registry_workspace"):
        st.markdown("#### :material/folder_open: Registru verificabil")
        st.caption("Caută, vizualizează și exportă documente împreună cu istoricul de audit.")
        st.page_link(
            registry_page,
            label="Deschide registrul",
            icon=":material/arrow_forward:",
        )

    st.markdown(
        '<div class="sodif-section-label">Încredere care poate fi mutată</div>',
        unsafe_allow_html=True,
    )
    capabilities = st.columns(3)
    content = (
        (
            "history",
            "Continuitatea reviziilor",
            "Fiecare versiune indică amprenta celei precedente; rupturile de lanț sunt respinse.",
        ),
        (
            "fingerprint",
            "Integritate la citire",
            "Conținutul este reverificat criptografic înainte de vizualizare sau descărcare.",
        ),
        (
            "inventory_2",
            "Dovadă portabilă",
            "Pachetul exportat permite verificarea independentă, fără acces la aplicație.",
        ),
    )
    for column, (icon, title, body) in zip(capabilities, content, strict=True):
        with column, st.container(border=True, key=f"archive_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)
