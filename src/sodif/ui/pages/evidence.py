"""Reports and verifiable-evidence page."""

from html import escape

import streamlit as st

from sodif.demo.models import FlightKind, FlightReport
from sodif.reporting import FlightExports, PersistedFlightRun
from sodif.ui.pages.shared import render_flight_summary, render_page_intro
from sodif.ui.presentation import present_flight
from sodif.ui.state import current_exports, current_persisted_run, current_report


def render_evidence_hub(control_page: str) -> None:
    """Render operational reports and audit exports for the active run."""
    render_page_intro(
        "Control operațional",
        "Audit și exporturi",
        "Consultă rezultatul ultimei rulări și exportă raportul operațional, jurnalul tehnic "
        "și manifestul de integritate.",
    )
    report = current_report()
    if report is None:
        _render_empty_state(control_page)
        return

    render_flight_summary(present_flight(report))
    exports = current_exports(report)
    _render_report_identity(report)
    _render_export_panel(exports, current_persisted_run(report))
    _render_package_contents()


def _render_empty_state(control_page: str) -> None:
    st.markdown(
        """
        <section class="sodif-empty-panel">
            <div class="sodif-ready-mark" aria-hidden="true"><span></span></div>
            <div><h2>Nicio rulare disponibilă</h2>
            <p>Pornește Security Flight sau Transversal Flight. Raportul Word, datele
            structurate, jurnalul tehnic și manifestul sunt create automat la final.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="empty_control_link"):
        st.page_link(
            control_page,
            label="Deschide centrul de control",
            icon=":material/play_arrow:",
            use_container_width=False,
        )


def _render_report_identity(report: FlightReport) -> None:
    flight_label = {
        FlightKind.SECURITY: "Security Flight",
        FlightKind.TRANSVERSAL: "Transversal Flight",
    }[report.flight_kind]
    st.markdown(
        f"""
        <section class="sodif-report-identity">
            <div><small>Rulare</small><code>{escape(report.report_id)}</code></div>
            <div><small>Flux</small><strong>{escape(flight_label)}</strong></div>
            <div><small>Organizație</small><strong>{escape(report.configuration.organization_name)}</strong></div>
            <div><small>Integritate</small><strong>SHA-256 verificabil</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_export_panel(
    exports: FlightExports,
    persisted: PersistedFlightRun | None,
) -> None:
    digest = f"{exports.bundle.digest[:25]}…{exports.bundle.digest[-10:]}"
    storage_status = (
        f"{len(persisted.artifacts)} fișiere arhivate automat"
        if persisted is not None
        else "Disponibil în sesiunea curentă"
    )
    st.markdown(
        f"""
        <section class="sodif-export-panel">
            <div><div class="sodif-card-caption">Pachet de audit</div>
            <h2>Arhiva rulării este disponibilă</h2>
            <p>Raport operațional, date structurate, jurnal tehnic și manifest de integritate,
            reunite într-un pachet portabil.</p></div>
            <div class="sodif-bundle-digest"><small>{escape(storage_status)}</small>
            <code>{escape(digest)}</code></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    bundle, document, structured, audit = st.columns(4)
    with bundle:
        st.download_button(
            "Pachet complet",
            data=exports.bundle.data,
            file_name=exports.bundle.filename,
            mime=exports.bundle.media_type,
            type="primary",
            icon=":material/archive:",
            use_container_width=True,
        )
    with document:
        st.download_button(
            "Raport Word",
            data=exports.document.data,
            file_name=exports.document.filename,
            mime=exports.document.media_type,
            icon=":material/description:",
            use_container_width=True,
        )
    with structured:
        st.download_button(
            "Date JSON",
            data=exports.report.data,
            file_name=exports.report.filename,
            mime=exports.report.media_type,
            icon=":material/data_object:",
            use_container_width=True,
        )
    with audit:
        st.download_button(
            "Jurnal de audit",
            data=exports.audit_log.data,
            file_name=exports.audit_log.filename,
            mime=exports.audit_log.media_type,
            icon=":material/receipt_long:",
            use_container_width=True,
        )


def _render_package_contents() -> None:
    st.markdown(
        '<div class="sodif-section-label">Conținutul pachetului</div>',
        unsafe_allow_html=True,
    )
    items = (
        ("description", "Raport operațional", "Decizii, controale și efecte asupra API."),
        ("data_object", "Date structurate", "Rezultatul complet, pregătit pentru procesare."),
        (
            "receipt_long",
            "Jurnal de audit",
            "Evenimente ordonate pentru integrare cu sisteme de audit.",
        ),
        (
            "verified",
            "Manifest de integritate",
            "Dimensiuni și amprente pentru verificarea fișierelor.",
        ),
    )
    columns = st.columns(4)
    for column, (icon, title, body) in zip(columns, items, strict=True):
        with column, st.container(border=True, key=f"evidence_item_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)
