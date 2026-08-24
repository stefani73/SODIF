"""Stable product copy derived from flight-domain evidence."""

from dataclasses import dataclass

from sodif.demo.models import FlightReport, FlightScenario, ScenarioOutcome, ScenarioResult


@dataclass(frozen=True, slots=True)
class ControlView:
    name: str
    state: str
    detail: str
    tone: str


@dataclass(frozen=True, slots=True)
class EvidenceView:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ScenarioView:
    scenario_id: FlightScenario
    kicker: str
    title: str
    summary: str
    verdict: str
    verdict_detail: str
    api_effect: str
    api_detail: str
    optimization_note: str
    tone: str
    controls: tuple[ControlView, ControlView, ControlView]
    timeline: tuple[str, ...]
    evidence: tuple[EvidenceView, ...]


@dataclass(frozen=True, slots=True)
class FlightView:
    title: str
    detail: str
    tone: str
    scenarios: tuple[ScenarioView, ...]


@dataclass(frozen=True, slots=True)
class _ScenarioCopy:
    kicker: str
    title: str
    summary: str
    verdict: str
    verdict_detail: str
    api_effect: str
    api_detail: str
    optimization_note: str


_SCENARIO_COPY = {
    FlightScenario.HAPPY_PATH: _ScenarioCopy(
        "Flux conform",
        "Comandă autentică și neambiguă",
        "Documentul semnat, valorile critice și acțiunea solicitată sunt consistente.",
        "Autorizată",
        "Dovezile independente confirmă aceeași intenție operațională.",
        "Cerere acceptată",
        "Permisul unic autorizează exact crearea comenzii aprobate.",
        "Verificarea s-a oprit imediat ce dovezile disponibile au devenit suficiente.",
    ),
    FlightScenario.ADAPTIVE_RECOVERY: _ScenarioCopy(
        "Verificare adaptivă",
        "Dovadă suplimentară necesară",
        "O valoare critică lipsește inițial, iar verificarea se extinde controlat.",
        "Autorizată",
        "Sursa suplimentară completează dovada fără a relaxa politica de siguranță.",
        "Cerere acceptată",
        "Execuția este permisă numai după confirmarea valorii lipsă.",
        "Resursele suplimentare sunt activate doar când traseul normal nu este concludent.",
    ),
    FlightScenario.TAMPERED_DOCUMENT: _ScenarioCopy(
        "Protecție de integritate",
        "Document modificat după semnare",
        "Conținutul primit nu mai corespunde reviziei acoperite de semnătură.",
        "Blocată",
        "Amprenta documentului diferă de cea semnată; procesarea se oprește imediat.",
        "Nicio cerere transmisă",
        "API-ul rămâne izolat de un document a cărui integritate a fost compromisă.",
        "Blocarea timpurie evită orice procesare semantică inutilă.",
    ),
    FlightScenario.SEMANTIC_CONFLICT: _ScenarioCopy(
        "Protecție semantică",
        "Valoare critică divergentă",
        "Reprezentările independente indică valori diferite pentru totalul aprobat.",
        "Revizuire necesară",
        "SODIF refuză să transforme o intenție ambiguă într-o acțiune executabilă.",
        "Execuție suspendată",
        "Niciun permis nu este emis până la clarificarea valorii critice.",
        "Escaladarea este limitată la conflictul care poate schimba efectul tranzacției.",
    ),
    FlightScenario.ACTION_TAMPERING: _ScenarioCopy(
        "Protecție a execuției",
        "Acțiune API modificată",
        "Ruta solicitată după autorizare diferă de acțiunea derivată din document.",
        "Blocată",
        "Legarea criptografică detectează abaterea dintre permis și cererea efectivă.",
        "Cerere respinsă",
        "Acțiunea modificată nu ajunge la sistemul operațional.",
        "Comparația exactă previne folosirea unei aprobări valide pentru altă acțiune.",
    ),
    FlightScenario.REPLAY_ATTACK: _ScenarioCopy(
        "Protecție anti-replay",
        "Permis prezentat din nou",
        "O autorizare deja consumată este reutilizată pentru repetarea tranzacției.",
        "Blocată",
        "Registrul de consum confirmă că permisul și-a produs deja efectul autorizat.",
        "Repetare respinsă",
        "API-ul este protejat împotriva unei a doua execuții a aceleiași aprobări.",
        "Controlul atomic păstrează unicitatea execuției chiar și la cereri concurente.",
    ),
}

_TIMELINE_COPY = {
    "revision-validated": "Autenticitatea documentului și revizia semnată au fost confirmate.",
    "risk-triaged": "Politica a ales nivelul adecvat de verificare pentru tranzacție.",
    "semantic-views": "Reprezentările independente ale documentului au fost confruntate.",
    "consensus-accepted": "Valorile critice au obținut consens verificabil.",
    "action-compiled": "Intenția aprobată a fost legată de acțiunea API exactă.",
    "permit-issued": "A fost emisă o autorizare criptografică de unică folosință.",
    "api-executed": "Sistemul operațional a acceptat acțiunea autorizată.",
    "document-blocked": "Diferența față de revizia semnată a oprit procesarea.",
    "consensus-escalated": "Conflictul critic a suspendat emiterea autorizării.",
    "action-blocked": "Abaterea față de acțiunea autorizată a fost respinsă.",
    "permit-consumed": "Prima utilizare validă a consumat autorizarea.",
    "replay-blocked": "Încercarea de reutilizare a fost respinsă.",
}


def present_flight(report: FlightReport) -> FlightView:
    """Translate technical evidence into concise, user-facing decisions."""
    return FlightView(
        title="Toate controalele au răspuns conform politicii",
        detail=(
            "Acțiunile conforme au fost autorizate, iar modificările, ambiguitățile și "
            "reutilizările au fost oprite înainte de sistemul operațional."
        ),
        tone="success" if report.passed else "danger",
        scenarios=tuple(present_scenario(result) for result in report.results),
    )


def present_scenario(result: ScenarioResult) -> ScenarioView:
    """Build the product view for one scenario without leaking engine vocabulary."""
    copy = _SCENARIO_COPY[result.scenario_id]
    tone = {
        ScenarioOutcome.EXECUTED: "success",
        ScenarioOutcome.BLOCKED: "danger",
        ScenarioOutcome.ESCALATED: "warning",
    }[result.observed_outcome]
    return ScenarioView(
        scenario_id=result.scenario_id,
        kicker=copy.kicker,
        title=copy.title,
        summary=copy.summary,
        verdict=copy.verdict,
        verdict_detail=copy.verdict_detail,
        api_effect=copy.api_effect,
        api_detail=copy.api_detail,
        optimization_note=copy.optimization_note,
        tone=tone,
        controls=_controls_for(result),
        timeline=tuple(_TIMELINE_COPY[item.stage] for item in result.observations),
        evidence=_evidence_for(result),
    )


def _controls_for(result: ScenarioResult) -> tuple[ControlView, ControlView, ControlView]:
    verified = ControlView(
        "Document",
        "Autentic",
        "Revizia și semnătura corespund.",
        "success",
    )
    consensus = ControlView(
        "Sens aprobat",
        "Confirmat",
        "Valorile critice sunt consistente.",
        "success",
    )
    executed = ControlView(
        "Execuție",
        "Autorizată",
        "Acțiunea exactă a primit permis unic.",
        "success",
    )
    if result.scenario_id is FlightScenario.TAMPERED_DOCUMENT:
        return (
            ControlView("Document", "Neconform", "Conținut diferit de revizia semnată.", "danger"),
            ControlView(
                "Sens aprobat", "Neprocesat", "Verificarea s-a oprit la integritate.", "neutral"
            ),
            ControlView("Execuție", "Blocată", "Nu a fost emisă nicio autorizare.", "danger"),
        )
    if result.scenario_id is FlightScenario.SEMANTIC_CONFLICT:
        return (
            verified,
            ControlView("Sens aprobat", "Neconcludent", "Valoare critică în conflict.", "warning"),
            ControlView("Execuție", "Suspendată", "Clarificarea este obligatorie.", "warning"),
        )
    if result.scenario_id is FlightScenario.ACTION_TAMPERING:
        return (
            verified,
            consensus,
            ControlView("Execuție", "Blocată", "Cererea diferă de permis.", "danger"),
        )
    if result.scenario_id is FlightScenario.REPLAY_ATTACK:
        return (
            verified,
            consensus,
            ControlView("Execuție", "Blocată", "Permisul fusese deja consumat.", "danger"),
        )
    if result.scenario_id is FlightScenario.ADAPTIVE_RECOVERY:
        consensus = ControlView(
            "Sens aprobat",
            "Confirmat extins",
            "Dovada lipsă a fost completată.",
            "success",
        )
    return verified, consensus, executed


def _evidence_for(result: ScenarioResult) -> tuple[EvidenceView, ...]:
    digests = tuple(
        item.subject_digest
        for item in result.observations
        if item.subject_digest is not None
    )
    evidence: list[EvidenceView] = []
    if result.verification is not None:
        evidence.append(
            EvidenceView("Document", _compact_digest(result.verification.revision_digest))
        )
    elif digests:
        evidence.append(EvidenceView("Document observat", _compact_digest(digests[0])))
    if result.permit_id is not None:
        evidence.append(EvidenceView("Permis", result.permit_id))
    if result.receipt is not None:
        evidence.extend(
            (
                EvidenceView("Acțiune", f"{result.receipt.method} {result.receipt.path}"),
                EvidenceView("Destinație", result.receipt.audience),
                EvidenceView("Confirmare API", str(result.receipt.response_code)),
            )
        )
    elif digests:
        evidence.append(EvidenceView("Dovadă decizie", _compact_digest(digests[-1])))
    return tuple(evidence)


def _compact_digest(value: str) -> str:
    return f"{value[:18]}…{value[-8:]}"
