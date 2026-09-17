"""Interactive control-center page."""

from collections.abc import Callable
from html import escape

import streamlit as st

from sodif.demo.models import FlightKind, FlightReport
from sodif.domain.enums import DocumentSecurityMode
from sodif.ui.pages.shared import render_flight_summary, render_page_intro
from sodif.ui.presentation import FlightView, ScenarioView, present_flight
from sodif.ui.state import current_report, current_run_error, run_assurance_demo

_ADVANCED_SECURITY_KEY = "sodif_advanced_security_enabled"
_ADVANCED_SECURITY_WIDGET_KEY = "sodif_control_advanced_security"


def render_control_center(
    security_runner: Callable[[DocumentSecurityMode], FlightReport],
    transversal_runner: Callable[[DocumentSecurityMode], FlightReport],
    reports_page: str,
    registry_page: str,
    gateway_page: str,
) -> None:
    """Run and explore the two product assurance flights."""
    render_page_intro(
        "Operațiuni",
        "Centru de control",
        "Execută traseul standard direct sau validarea protecției avansate prin SODIF "
        "Security, SODIF Archive și SODIF Gateway.",
    )
    security_mode = _render_security_mode_selector()
    security, transversal = st.columns(2, gap="large")
    with security, st.container(border=True, key="security_flight_card"):
        st.markdown(
            """
            <section class="sodif-flight-choice">
                <div class="sodif-assurance-label"><span></span>Nucleul de securitate</div>
                <h2>Security Flight</h2>
                <p>Acoperă SODIF Security: semnătură, verificare adaptivă, consens,
                permis unic și controlul acțiunii API.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Rulează Security Flight",
            type="primary",
            icon=":material/play_arrow:",
            disabled=security_mode is DocumentSecurityMode.STANDARD,
            use_container_width=True,
            on_click=run_assurance_demo,
            args=(FlightKind.SECURITY, security_runner, DocumentSecurityMode.ADVANCED),
        )
    with transversal, st.container(border=True, key="transversal_flight_card"):
        transversal_detail = (
            "SODIF Security, SODIF Archive și SODIF Gateway funcționează împreună până "
            "la decizia și efectul API."
            if security_mode is DocumentSecurityMode.ADVANCED
            else "Semnătura și arhivarea sunt urmate de transferul direct al datelor "
            "configurate către adaptorul API."
        )
        st.markdown(
            f"""
            <section class="sodif-flight-choice">
                <div class="sodif-assurance-label"><span></span>Lanț end-to-end</div>
                <h2>Transversal Flight</h2>
                <p>{escape(transversal_detail)}</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Rulează Transversal Flight",
            icon=":material/account_tree:",
            use_container_width=True,
            on_click=run_assurance_demo,
            args=(FlightKind.TRANSVERSAL, transversal_runner, security_mode),
        )

    run_error = current_run_error()
    if run_error is not None:
        st.error(run_error, icon=":material/gpp_bad:")

    report = current_report()
    if report is None:
        _render_ready_state(security_mode)
        return

    view = present_flight(report)
    _render_active_flight(report)
    render_flight_summary(view)
    reports_shortcut, registry_shortcut, gateway_shortcut, spacer = st.columns(
        (0.22, 0.22, 0.22, 0.34)
    )
    with reports_shortcut, st.container(key="reports_shortcut"):
        st.page_link(
            reports_page,
            label="Deschide rapoartele",
            icon=":material/fact_check:",
            use_container_width=True,
        )
    with registry_shortcut:
        if report.flight_kind is FlightKind.TRANSVERSAL:
            with st.container(key="registry_shortcut"):
                st.page_link(
                    registry_page,
                    label="Deschide registrul",
                    icon=":material/folder_open:",
                    use_container_width=True,
                )
    with gateway_shortcut:
        if (
            report.flight_kind is FlightKind.TRANSVERSAL
            and report.security_mode is DocumentSecurityMode.ADVANCED
        ):
            with st.container(key="gateway_shortcut"):
                st.page_link(
                    gateway_page,
                    label="Deschide Gateway-ul",
                    icon=":material/hub:",
                    use_container_width=True,
                )
    with spacer:
        st.markdown(
            '<p class="sodif-inline-note">Raportul operațional și jurnalul de audit au fost '
            "generate automat pentru această rulare.</p>",
            unsafe_allow_html=True,
        )
    _render_scenario_explorer(view)


def _render_security_mode_selector() -> DocumentSecurityMode:
    st.markdown(
        '<div class="sodif-section-label compact">Regim de execuție</div>',
        unsafe_allow_html=True,
    )
    selected = st.session_state.get(_ADVANCED_SECURITY_KEY, True)
    enabled = st.checkbox(
        "Activează protecția avansată SODIF pentru această rulare",
        value=bool(selected),
        key=_ADVANCED_SECURITY_WIDGET_KEY,
        help=(
            "Activează consensul semantic, dovada criptografică, permisul unic și controlul "
            "Gateway înaintea transferului către API."
        ),
    )
    st.session_state[_ADVANCED_SECURITY_KEY] = enabled
    if enabled:
        st.caption("Transversal Flight aplică întregul lanț SODIF înaintea transferului către API.")
        return DocumentSecurityMode.ADVANCED
    st.caption(
        "Transversal Flight folosește traseul standard: semnătură și arhivare, urmate de "
        "transferul direct al datelor configurate către adaptorul API."
    )
    return DocumentSecurityMode.STANDARD


def _render_ready_state(security_mode: DocumentSecurityMode) -> None:
    if security_mode is DocumentSecurityMode.ADVANCED:
        detail = (
            "Alege nucleul de securitate sau lanțul transversal care conectează toate "
            "cele trei module ale platformei."
        )
    else:
        detail = (
            "Rulează traseul transversal standard pentru a demonstra transferul direct "
            "către adaptorul API."
        )
    st.markdown(
        f"""
        <section class="sodif-ready-panel">
            <div class="sodif-ready-mark" aria-hidden="true"><span></span></div>
            <div><h2>Sistem pregătit</h2>
            <p>{escape(detail)}</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    capabilities = (
        (
            (
                "SODIF Security",
                "Semnătură, consens, intenție și permis unic",
            ),
            ("SODIF Archive", "Revizii și istoric verificabil"),
            ("SODIF Gateway", "Legare exactă, rutare și blocare controlată"),
        )
        if security_mode is DocumentSecurityMode.ADVANCED
        else (
            ("Semnătură", "Autenticitatea și integritatea reviziei"),
            ("SODIF Archive", "Revizii păstrate în regim standard"),
            ("Adaptor API", "Transfer direct al datelor configurate"),
        )
    )
    for column, (title, body) in zip(columns, capabilities, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-capability"><b>{escape(title)}</b>'
                f"<span>{escape(body)}</span></article>",
                unsafe_allow_html=True,
            )


def _render_active_flight(report: FlightReport) -> None:
    label, detail = {
        FlightKind.SECURITY: (
            "Security Flight",
            "Semnătură și execuție controlată",
        ),
        FlightKind.TRANSVERSAL: (
            "Transversal Flight",
            "SODIF Security, SODIF Archive și SODIF Gateway",
        ),
    }[report.flight_kind]
    if report.security_mode is DocumentSecurityMode.STANDARD:
        detail = "Semnătură, arhivare și transfer direct către adaptorul API"
    st.markdown(
        f'<div class="sodif-flight-active"><strong>{escape(label)}</strong>'
        f"<span>{escape(detail)}</span></div>",
        unsafe_allow_html=True,
    )


def _render_scenario_explorer(view: FlightView) -> None:
    st.markdown(
        '<div class="sodif-section-label">Tranzacții evaluate</div>', unsafe_allow_html=True
    )
    labels = {scenario.scenario_id: scenario.title for scenario in view.scenarios}
    selected_id = st.selectbox(
        "Situația analizată",
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
                <div class="sodif-card-caption">Motivul deciziei</div>
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
                <div class="sodif-card-caption">Efect asupra API-ului</div>
                <h3>{escape(scenario.api_effect)}</h3>
                <p>{escape(scenario.api_detail)}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )

    if scenario.comparisons:
        _render_field_comparisons(scenario)

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
            '<div class="sodif-subsection-title">Identificatori și trasabilitate</div>',
            unsafe_allow_html=True,
        )
        evidence_html = "".join(
            f'<div class="sodif-evidence-row"><span>{escape(item.label)}</span>'
            f"<code>{escape(item.value)}</code></div>"
            for item in scenario.evidence
        )
        st.markdown(f'<div class="sodif-evidence">{evidence_html}</div>', unsafe_allow_html=True)


def _render_field_comparisons(scenario: ScenarioView) -> None:
    st.markdown(
        '<div class="sodif-subsection-title">Valorile confruntate și rezultatul</div>',
        unsafe_allow_html=True,
    )
    cards = []
    for comparison in scenario.comparisons:
        observations = "".join(
            f"<li>{escape(observation)}</li>" for observation in comparison.observations
        )
        cards.append(
            f'<article class="sodif-comparison-card {comparison.tone}">'
            "<small>Câmp operațional</small>"
            f"<h3>{escape(comparison.label)}</h3>"
            f"<ul>{observations}</ul>"
            f"<strong>{escape(comparison.conclusion)}</strong>"
            "</article>"
        )
    st.markdown(
        '<div class="sodif-comparison-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="sodif-data-path">
            <span>Document validat</span><i></i><span>Valori confruntate</span><i></i>
            <span>Parametri API</span><i></i><span>Amprentă și permis</span>
        </div>
        <p class="sodif-inline-note">Valorile acceptate devin parametrii cererii API. Metoda,
        ruta și destinația provin din politica operațională activă; planul rezultat este
        amprentat, iar amprenta este inclusă în permisul semnat.</p>
        """,
        unsafe_allow_html=True,
    )
