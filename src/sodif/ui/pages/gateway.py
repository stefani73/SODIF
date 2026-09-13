"""SODIF Gateway product workspace."""

from html import escape

import streamlit as st

from sodif.domain.gateway import GatewayCheckOutcome, GatewayDecision, GatewayDecisionStatus
from sodif.gateway.sample import GatewaySampleScenario, run_gateway_sample
from sodif.product import product_module
from sodif.settings import GatewaySettings
from sodif.ui.pages.shared import render_module_contract, render_module_intro

_RESULTS_KEY = "sodif_gateway_workspace_results"
_SCENARIO_LABELS = {
    GatewaySampleScenario.CONFORMING: "Tranzacție conformă",
    GatewaySampleScenario.CHANGED_ACTION: "Parametri modificați după aprobare",
    GatewaySampleScenario.REPLAYED: "Permis prezentat a doua oară",
}
_SCENARIO_DESCRIPTIONS = {
    GatewaySampleScenario.CONFORMING: (
        "Cererea corespunde integral acțiunii aprobate și poate fi rutată o singură dată."
    ),
    GatewaySampleScenario.CHANGED_ACTION: (
        "Valoarea totală din cerere diferă de valoarea legată criptografic de permis."
    ),
    GatewaySampleScenario.REPLAYED: (
        "Aceeași autorizare este prezentată din nou după consumarea primei execuții."
    ),
}
_CHECK_LABELS = {
    "route.resolved": "Rută cunoscută",
    "route.audience": "Destinație corectă",
    "route.method": "Metodă permisă",
    "route.path": "Resursă protejată",
    "request.size": "Complexitate acceptată",
    "permit.authorization": "Permis valid și unic",
    "upstream.execution": "Execuție acceptată",
}
_PASSED_CHECK_DETAILS = {
    "route.resolved": "Ruta este configurată și disponibilă pentru control.",
    "route.audience": "Cererea vizează serviciul protejat de această rută.",
    "route.method": "Metoda HTTP este permisă de politica rutei.",
    "route.path": "Resursa solicitată se află în limita protejată.",
    "request.size": "Cererea respectă limita de complexitate configurată.",
    "permit.authorization": (
        "Semnătura, valabilitatea, acțiunea, destinația și utilizarea unică sunt valide."
    ),
    "upstream.execution": "Serviciul protejat a acceptat tranzacția autorizată.",
}
_FAILED_CHECK_DETAILS = {
    "route.resolved": "Ruta solicitată nu este configurată.",
    "route.audience": "Cererea vizează un alt serviciu decât cel protejat.",
    "route.method": "Metoda HTTP nu este permisă pe această rută.",
    "route.path": "Resursa solicitată este în afara limitei protejate.",
    "request.size": "Cererea depășește limita de complexitate configurată.",
    "upstream.execution": "Adaptorul serviciului protejat a refuzat tranzacția.",
}


def render_gateway_module(settings: GatewaySettings) -> None:
    """Present and exercise the gateway enforcement boundary."""
    module = product_module("gateway")
    render_module_intro(module)
    render_module_contract(module)
    _render_policy_workspace(settings)

    st.markdown(
        '<div class="sodif-section-label">Politici aplicate tranzacției</div>',
        unsafe_allow_html=True,
    )
    policies = (
        (
            "route",
            "Potrivire exactă",
            "Metoda, ruta și parametrii cererii trebuie să coincidă cu acțiunea autorizată.",
        ),
        (
            "domain_verification",
            "Destinație controlată",
            "Permisul este acceptat numai de serviciul pentru care a fost emis.",
        ),
        (
            "timer",
            "Fereastră limitată",
            "Expirarea și consumul unic reduc suprafața de abuz a unei aprobări valide.",
        ),
        (
            "policy_alert",
            "Blocare motivată",
            "Orice abatere produce o decizie explicită, o urmă de audit și oprirea "
            "cererii înainte de API.",
        ),
    )
    columns = st.columns(4)
    for column, (icon, title, body) in zip(columns, policies, strict=True):
        with column, st.container(border=True, key=f"gateway_{icon}"):
            st.markdown(f"#### :material/{icon}: {title}")
            st.caption(body)

    st.markdown(
        """
        <section class="sodif-gateway-flow">
            <div><small>Cerere</small><strong>Apel API + permis</strong>
            <span>Tranzacția pregătită pentru execuție</span></div>
            <i aria-hidden="true"></i>
            <div class="active"><small>Control</small>
            <strong>SODIF Gateway</strong>
            <span>Identitate, intenție, destinație și unicitate</span></div>
            <i aria-hidden="true"></i>
            <div><small>Rezultat</small><strong>Rutare / blocare</strong>
            <span>Decizie justificată și auditabilă</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="sodif-boundary-panel">
            <div><div class="sodif-section-label light">Integrare pragmatică</div>
            <h2>Control integrabil în infrastructura API existentă.</h2></div>
            <p>SODIF Gateway aplică politicile tehnice ale rutei și verifică dreptul
            tranzacțional derivat din documentul semnat.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_policy_workspace(settings: GatewaySettings) -> None:
    st.markdown(
        '<div class="sodif-section-label compact">Gateway Policy Studio</div>',
        unsafe_allow_html=True,
    )
    configuration, evaluation = st.columns((0.38, 0.62))
    with configuration:
        st.markdown(
            f"""
            <section class="sodif-gateway-route">
                <small>Rută protejată</small><h2>{escape(settings.route_id)}</h2>
                <div><span>Serviciu</span><strong>{escape(settings.audience)}</strong></div>
                <div><span>Resursă</span><strong>POST {escape(settings.path_prefix)}</strong></div>
                <div><span>Politică</span><strong>Acțiune exactă · utilizare unică</strong></div>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with evaluation:
        selected_label = st.selectbox(
            "Tranzacția evaluată",
            options=tuple(_SCENARIO_LABELS.values()),
        )
        scenario = next(item for item, label in _SCENARIO_LABELS.items() if label == selected_label)
        st.markdown(
            f'<p class="sodif-gateway-scenario">{escape(_SCENARIO_DESCRIPTIONS[scenario])}</p>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Evaluează tranzacția",
            type="primary",
            icon=":material/policy:",
            use_container_width=True,
        ):
            results = dict(st.session_state.get(_RESULTS_KEY, {}))
            results[scenario.value] = run_gateway_sample(scenario, settings)
            st.session_state[_RESULTS_KEY] = results

    stored = st.session_state.get(_RESULTS_KEY, {})
    decision = stored.get(scenario.value) if isinstance(stored, dict) else None
    if isinstance(decision, GatewayDecision):
        _render_gateway_decision(decision)
    else:
        st.markdown(
            """
            <section class="sodif-gateway-ready">
                <span aria-hidden="true"></span><div><small>Policy engine</small>
                <h2>Pregătit pentru evaluarea tranzacției</h2>
                <p>Rezultatul va indica efectul asupra API-ului și controlul care a decis.</p>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )


def _render_gateway_decision(decision: GatewayDecision) -> None:
    routed = decision.status is GatewayDecisionStatus.ROUTED
    tone = "success" if routed else "danger"
    title = "Tranzacție autorizată" if routed else "Tranzacție blocată"
    effect = f"Rutată · HTTP {decision.receipt.response_code}" if decision.receipt else "Oprită"
    st.markdown(
        f"""
        <section class="sodif-gateway-decision {tone}">
            <div class="sodif-gateway-decision-head"><span aria-hidden="true"></span><div>
            <small>Decizie Gateway</small><h2>{escape(title)}</h2>
            <p>{escape(_decision_explanation(decision))}</p></div></div>
            <div class="sodif-gateway-decision-meta">
                <div><small>Rută</small><strong>{escape(decision.route_id)}</strong></div>
                <div><small>Destinație</small><strong>{escape(decision.audience)}</strong></div>
                <div><small>Efect API</small><strong>{escape(effect)}</strong></div>
                <div><small>Decizie</small><strong>{escape(decision.decision_id)}</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    for check in decision.checks:
        passed = check.outcome is GatewayCheckOutcome.PASSED
        state = "passed" if passed else "failed"
        label = _CHECK_LABELS.get(check.code, check.code)
        detail = _check_explanation(check.code, passed, decision)
        st.markdown(
            f"""
            <div class="sodif-gateway-check {state}"><span aria-hidden="true"></span>
            <p><strong>{escape(label)}</strong><small>{escape(detail)}</small></p></div>
            """,
            unsafe_allow_html=True,
        )
    st.download_button(
        "Exportă decizia JSON",
        data=decision.model_dump_json(indent=2),
        file_name=f"{decision.decision_id}.json",
        mime="application/json",
        icon=":material/download:",
        use_container_width=False,
    )


def _decision_explanation(decision: GatewayDecision) -> str:
    explanations = {
        "route.authorized": "Cererea coincide cu permisul și a fost executată o singură dată.",
        "permit.action_mismatch": (
            "Parametrii cererii diferă de tranzacția autorizată în documentul semnat."
        ),
        "permit.permit_replayed": "Permisul a fost deja consumat de o execuție anterioară.",
    }
    return explanations.get(decision.code, decision.detail)


def _check_explanation(code: str, passed: bool, decision: GatewayDecision) -> str:
    if passed:
        return _PASSED_CHECK_DETAILS.get(code, "Control îndeplinit.")
    if code == "permit.authorization":
        return _decision_explanation(decision)
    return _FAILED_CHECK_DETAILS.get(code, "Control neîndeplinit; tranzacția a fost oprită.")
