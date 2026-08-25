"""Interactive control-center page."""

from collections.abc import Callable
from html import escape

import streamlit as st

from sodif.demo.models import FlightKind, FlightReport
from sodif.ui.pages.shared import render_flight_summary, render_page_intro
from sodif.ui.presentation import FlightView, ScenarioView, present_flight
from sodif.ui.state import current_report, run_assurance_demo


def render_control_center(
    security_runner: Callable[[], FlightReport],
    transversal_runner: Callable[[], FlightReport],
    reports_page: str,
    registry_page: str,
    gateway_page: str,
) -> None:
    """Run and explore the two product assurance flights."""
    render_page_intro(
        "Operațiuni",
        "Centru de control",
        "Validează separat nucleul de securitate sau întregul lanț de încredere prin "
        "securitatea intenției, arhiva verificabilă și Gateway-ul semantic.",
    )
    security, transversal = st.columns(2, gap="large")
    with security, st.container(border=True, key="security_flight_card"):
        st.markdown(
            """
            <section class="sodif-flight-choice">
                <div class="sodif-assurance-label"><span></span>Nucleul de securitate</div>
                <h2>Security Flight</h2>
                <p>Semnătură, verificare adaptivă a intenției, permis unic și protecția
                acțiunii API — fără componenta DMS.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Rulează Security Flight",
            type="primary",
            icon=":material/play_arrow:",
            use_container_width=True,
            on_click=run_assurance_demo,
            args=(FlightKind.SECURITY, security_runner),
        )
    with transversal, st.container(border=True, key="transversal_flight_card"):
        st.markdown(
            """
            <section class="sodif-flight-choice">
                <div class="sodif-assurance-label"><span></span>Lanț end-to-end</div>
                <h2>Transversal Flight</h2>
                <p>Securitatea intenției, arhiva documentară verificabilă și Gateway-ul
                semantic funcționează împreună până la decizia API.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Rulează Transversal Flight",
            icon=":material/account_tree:",
            use_container_width=True,
            on_click=run_assurance_demo,
            args=(FlightKind.TRANSVERSAL, transversal_runner),
        )

    report = current_report()
    if report is None:
        _render_ready_state()
        return

    view = present_flight(report)
    _render_active_flight(report.flight_kind)
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
        if report.flight_kind is FlightKind.TRANSVERSAL:
            with st.container(key="gateway_shortcut"):
                st.page_link(
                    gateway_page,
                    label="Deschide Gateway-ul",
                    icon=":material/hub:",
                    use_container_width=True,
                )
    with spacer:
        st.markdown(
            '<p class="sodif-inline-note">Rezultatele și exporturile provin din '
            "aceeași rulare.</p>",
            unsafe_allow_html=True,
        )
    _render_scenario_explorer(view)


def _render_ready_state() -> None:
    st.markdown(
        """
        <section class="sodif-ready-panel">
            <div class="sodif-ready-mark" aria-hidden="true"><span></span></div>
            <div><h2>Sistem pregătit</h2>
            <p>Alege nucleul de securitate sau lanțul transversal care conectează toate
            cele trei module ale platformei.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    capabilities = (
        ("Securitate", "Validarea semnăturii, intenției și permisului unic"),
        ("Trasabilitate", "Păstrarea reviziilor și dovezilor verificabile"),
        ("Control API", "Rutare semantică exactă și blocare fail-closed"),
    )
    for column, (title, body) in zip(columns, capabilities, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-capability"><b>{escape(title)}</b>'
                f"<span>{escape(body)}</span></article>",
                unsafe_allow_html=True,
            )


def _render_active_flight(kind: FlightKind) -> None:
    label, detail = {
        FlightKind.SECURITY: (
            "Security Flight",
            "Semnătură și execuție controlată",
        ),
        FlightKind.TRANSVERSAL: (
            "Transversal Flight",
            "Securitate, arhivă verificabilă și Gateway semantic",
        ),
    }[kind]
    st.markdown(
        f'<div class="sodif-flight-active"><strong>{escape(label)}</strong>'
        f"<span>{escape(detail)}</span></div>",
        unsafe_allow_html=True,
    )


def _render_scenario_explorer(view: FlightView) -> None:
    st.markdown(
        '<div class="sodif-section-label">Situații verificate</div>', unsafe_allow_html=True
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
            '<div class="sodif-subsection-title">Dovezi verificabile</div>',
            unsafe_allow_html=True,
        )
        evidence_html = "".join(
            f'<div class="sodif-evidence-row"><span>{escape(item.label)}</span>'
            f"<code>{escape(item.value)}</code></div>"
            for item in scenario.evidence
        )
        st.markdown(f'<div class="sodif-evidence">{evidence_html}</div>', unsafe_allow_html=True)
