"""Product-oriented Streamlit experience for SODIF."""

from collections.abc import Callable
from html import escape

import streamlit as st

from sodif.demo.models import FlightReport
from sodif.demo.runner import run_default_flight
from sodif.reporting import FlightExports, build_flight_exports
from sodif.settings import AppSettings
from sodif.ui.presentation import FlightView, ScenarioView, present_flight
from sodif.ui.styles import PRODUCT_STYLES

HOME = "Prezentare"
FLIGHT = "Assurance Flight"


def configure_page(settings: AppSettings) -> None:
    """Apply browser metadata before rendering any UI element."""
    st.set_page_config(
        page_title=f"{settings.app_name} | Signed Intent Control",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={},
    )


def render_product_shell(
    settings: AppSettings,
    flight_runner: Callable[[], FlightReport] = run_default_flight,
) -> None:
    """Render the complete landing and assurance-flight product surfaces."""
    st.markdown(PRODUCT_STYLES, unsafe_allow_html=True)
    _render_header(settings)

    selected_view = st.radio(
        "Navigare principală",
        (HOME, FLIGHT),
        horizontal=True,
        label_visibility="collapsed",
        key="sodif_navigation",
    )
    st.markdown('<div class="sodif-nav-rule"></div>', unsafe_allow_html=True)

    if selected_view == HOME:
        _render_landing(settings)
    else:
        _render_assurance_flight(flight_runner)


def _render_header(settings: AppSettings) -> None:
    name = escape(settings.app_name)
    st.markdown(
        f"""
        <div class="sodif-header">
            <div class="sodif-brand">
                <span class="sodif-mark" aria-hidden="true"><i></i></span>
                <span class="sodif-wordmark">{name}</span>
            </div>
            <div class="sodif-trust-chip"><span></span> Signed Intent Control</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _open_flight() -> None:
    st.session_state["sodif_navigation"] = FLIGHT


def _render_landing(settings: AppSettings) -> None:
    st.markdown(
        """
        <section class="sodif-hero">
            <div class="sodif-eyebrow">Document-to-API trust layer</div>
            <h1>Din document semnat în acțiune digitală de încredere.</h1>
            <p class="sodif-lead">SODIF verifică sensul aprobat, îl leagă criptografic de
            acțiunea API exactă și împiedică modificarea sau repetarea execuției.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    cta, promise = st.columns((0.28, 0.72), vertical_alignment="center")
    with cta:
        st.button(
            "Deschide Assurance Flight",
            type="primary",
            use_container_width=True,
            on_click=_open_flight,
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
        ("Sens confirmat", "Valorile critice sunt confruntate între reprezentări independente."),
        ("Permis unic", "Consensul este legat de acțiunea API exactă și de destinația ei."),
        ("Execuție controlată", "Orice modificare sau reutilizare este respinsă înainte de API."),
    )
    for column, (title, body) in zip(columns, chain, strict=True):
        with column:
            st.markdown(
                f"""
                <article class="sodif-chain-card">
                    <div class="sodif-card-signal"><span></span></div>
                    <h3>{title}</h3><p>{body}</p>
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
                <div><span>✓</span><p><b>Integritate</b>
                <small>Blochează documentele modificate după semnare</small></p></div>
                <div><span>✓</span><p><b>Claritate</b>
                <small>Oprește valorile critice aflate în conflict</small></p></div>
                <div><span>✓</span><p><b>Precizie</b>
                <small>Respinge parametrii API diferiți de cei autorizați</small></p></div>
                <div><span>✓</span><p><b>Unicitate</b>
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
        ("Procurement", "Comenzile de achiziție semnate devin cereri ERP controlate."),
        ("Operațiuni reglementate", "Aprobările formale autorizează numai acțiunea prevăzută."),
        (
            "Integrare inter-organizații",
            "Documentele semnate coordonează API-uri fără încredere implicită.",
        ),
    )
    for column, (title, body) in zip(use_cases, cases, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-use-card"><h3>{title}</h3><p>{body}</p></article>',
                unsafe_allow_html=True,
            )


def _run_flight(flight_runner: Callable[[], FlightReport]) -> None:
    report = flight_runner()
    st.session_state["sodif_flight_report"] = report
    st.session_state["sodif_flight_exports"] = build_flight_exports(report)


def _render_assurance_flight(flight_runner: Callable[[], FlightReport]) -> None:
    intro, action = st.columns((0.72, 0.28), vertical_alignment="bottom")
    with intro:
        st.markdown(
            """
            <div class="sodif-eyebrow">Control Center</div>
            <h1 class="sodif-page-title">Assurance Flight</h1>
            <p class="sodif-page-lead">Demonstrație controlată a deciziilor SODIF pentru o
            comandă de achiziție transmisă către un API operațional.</p>
            """,
            unsafe_allow_html=True,
        )
    with action:
        st.button(
            "Pornește verificarea",
            type="primary",
            use_container_width=True,
            on_click=_run_flight,
            args=(flight_runner,),
        )

    report = st.session_state.get("sodif_flight_report")
    if not isinstance(report, FlightReport):
        _render_flight_ready_state()
        return

    view = present_flight(report)
    _render_flight_summary(view)
    exports = st.session_state.get("sodif_flight_exports")
    if not isinstance(exports, FlightExports):
        exports = build_flight_exports(report)
        st.session_state["sodif_flight_exports"] = exports
    _render_export_panel(exports)
    _render_scenario_explorer(view)


def _render_flight_ready_state() -> None:
    st.markdown(
        """
        <section class="sodif-ready-panel">
            <div class="sodif-ready-mark">◈</div>
            <div><h2>Pregătit pentru verificare</h2>
            <p>Flight-ul urmărește traseul complet de la documentul semnat până la decizia
            de execuție și demonstrează comportamentul sigur în situații neconforme.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    capabilities = (
        ("Autenticitate", "Validarea reviziei acoperite de semnătură"),
        ("Consens", "Confirmarea adaptivă a valorilor critice"),
        ("Execuție", "Autorizare exactă și protecție anti-replay"),
    )
    for column, (title, body) in zip(columns, capabilities, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-capability"><b>{title}</b><span>{body}</span></article>',
                unsafe_allow_html=True,
            )


def _render_flight_summary(view: FlightView) -> None:
    st.markdown(
        f"""
        <section class="sodif-flight-summary {view.tone}">
            <span class="sodif-summary-icon">✓</span>
            <div><div class="sodif-summary-kicker">Rezultat verificare</div>
            <h2>{escape(view.title)}</h2><p>{escape(view.detail)}</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_export_panel(exports: FlightExports) -> None:
    digest = f"{exports.bundle.digest[:25]}…{exports.bundle.digest[-10:]}"
    st.markdown(
        f"""
        <section class="sodif-export-panel">
            <div><div class="sodif-card-caption">Evidence package</div>
            <h2>Dovezile sunt pregătite pentru preluare</h2>
            <p>Raport pentru analiză umană, reprezentare structurată, jurnal auditabil și
            manifest de integritate, reunite într-un singur pachet.</p></div>
            <div class="sodif-bundle-digest"><small>Amprentă pachet</small>
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
            use_container_width=True,
        )
    with document:
        st.download_button(
            "Raport Word",
            data=exports.document.data,
            file_name=exports.document.filename,
            mime=exports.document.media_type,
            use_container_width=True,
        )
    with structured:
        st.download_button(
            "Dovezi JSON",
            data=exports.report.data,
            file_name=exports.report.filename,
            mime=exports.report.media_type,
            use_container_width=True,
        )
    with audit:
        st.download_button(
            "Jurnal audit",
            data=exports.audit_log.data,
            file_name=exports.audit_log.filename,
            mime=exports.audit_log.media_type,
            use_container_width=True,
        )


def _render_scenario_explorer(view: FlightView) -> None:
    st.markdown('<div class="sodif-section-label">Decizii evaluate</div>', unsafe_allow_html=True)
    labels = {scenario.scenario_id: scenario.title for scenario in view.scenarios}
    selected_id = st.selectbox(
        "Alege situația analizată",
        tuple(labels),
        format_func=labels.__getitem__,
    )
    scenario = next(item for item in view.scenarios if item.scenario_id == selected_id)
    _render_scenario(scenario)


def _render_scenario(scenario: ScenarioView) -> None:
    st.markdown(
        f"""
        <section class="sodif-scenario-head">
            <div><div class="sodif-scenario-kicker">{escape(scenario.kicker)}</div>
            <h2>{escape(scenario.title)}</h2><p>{escape(scenario.summary)}</p></div>
            <div class="sodif-verdict {scenario.tone}"><small>Decizie</small>
            <b>{escape(scenario.verdict)}</b></div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    control_columns = st.columns(3)
    for column, control in zip(control_columns, scenario.controls, strict=True):
        with column:
            st.markdown(
                f"""
                <article class="sodif-control-card {control.tone}">
                    <div><span></span>{escape(control.name)}</div>
                    <h3>{escape(control.state)}</h3><p>{escape(control.detail)}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )

    decision, api = st.columns(2)
    with decision:
        st.markdown(
            f"""
            <article class="sodif-decision-card">
                <div class="sodif-card-caption">Rațiunea deciziei</div>
                <h3>{escape(scenario.verdict_detail)}</h3>
                <p>{escape(scenario.optimization_note)}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )
    with api:
        st.markdown(
            f"""
            <article class="sodif-decision-card accent">
                <div class="sodif-card-caption">Efect asupra API</div>
                <h3>{escape(scenario.api_effect)}</h3>
                <p>{escape(scenario.api_detail)}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )

    timeline, evidence = st.columns((0.58, 0.42))
    with timeline:
        st.markdown(
            '<div class="sodif-subsection-title">Traseul deciziei</div>', unsafe_allow_html=True
        )
        timeline_html = "".join(
            f'<div class="sodif-timeline-item"><span></span><p>{escape(item)}</p></div>'
            for item in scenario.timeline
        )
        st.markdown(f'<div class="sodif-timeline">{timeline_html}</div>', unsafe_allow_html=True)
    with evidence:
        st.markdown(
            '<div class="sodif-subsection-title">Dovezi verificabile</div>', unsafe_allow_html=True
        )
        evidence_html = "".join(
            f'<div class="sodif-evidence-row"><span>{escape(item.label)}</span>'
            f"<code>{escape(item.value)}</code></div>"
            for item in scenario.evidence
        )
        st.markdown(f'<div class="sodif-evidence">{evidence_html}</div>', unsafe_allow_html=True)
