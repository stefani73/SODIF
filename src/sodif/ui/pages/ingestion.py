"""Professional signed-document ingestion surface."""

from html import escape

import streamlit as st
from pydantic import ValidationError

from sodif.archive import (
    ArchiveConflict,
    ArchiveError,
    IngestionReceipt,
    SignedDocumentIngestionService,
)
from sodif.archive.sample import (
    SAMPLE_DOCUMENT_ID,
    SAMPLE_SEQUENCE_ZIP_NAME,
    SignedSampleSequence,
    build_signed_sample_sequence,
)
from sodif.documents import DocumentRejected, DocumentRejectionCode
from sodif.domain.enums import DocumentSecurityMode
from sodif.domain.revisions import SignedRevision
from sodif.ui.pages.shared import render_page_intro

_RECEIPT_KEY = "sodif_ingestion_receipt"
_ERROR_KEY = "sodif_ingestion_error"
_ADVANCED_SECURITY_KEY = "sodif_advanced_security_enabled"
_ADVANCED_SECURITY_WIDGET_KEY = "sodif_ingestion_advanced_security"

_REJECTION_MESSAGES = {
    DocumentRejectionCode.INVALID_BINARY_INPUT: "Fișierul încărcat nu poate fi procesat.",
    DocumentRejectionCode.EMPTY_DOCUMENT: "Documentul încărcat este gol.",
    DocumentRejectionCode.DOCUMENT_TOO_LARGE: "Documentul depășește limita acceptată.",
    DocumentRejectionCode.MALFORMED_PDF: "Fișierul nu este un document PDF valid.",
    DocumentRejectionCode.CONTENT_DIGEST_MISMATCH: (
        "Documentul nu corespunde conținutului acoperit de semnătură."
    ),
    DocumentRejectionCode.UNTRUSTED_KEY: "Cheia folosită pentru semnare nu este de încredere.",
    DocumentRejectionCode.SIGNER_KEY_MISMATCH: (
        "Semnatarul declarat nu corespunde cheii de semnare."
    ),
    DocumentRejectionCode.KEY_NOT_ACTIVE: "Cheia nu era activă la momentul semnării.",
    DocumentRejectionCode.KEY_REVOKED: "Cheia era revocată la momentul semnării.",
    DocumentRejectionCode.SIGNING_TIME_INVALID: "Momentul semnării nu este valid.",
    DocumentRejectionCode.SIGNATURE_INVALID: "Semnătura documentului nu este validă.",
    DocumentRejectionCode.REVISION_CHAIN_INVALID: (
        "Revizia nu continuă istoricul documentului sau intră în conflict cu acesta."
    ),
}


def render_document_ingestion(service: SignedDocumentIngestionService) -> None:
    """Render upload, validation, archive receipt and signed sample actions."""
    render_page_intro(
        "Documente",
        "Preluare documente",
        "Încarcă documentul PDF și dovada semnăturii. SODIF verifică autenticitatea, "
        "integritatea și continuitatea reviziei înainte de arhivare.",
    )

    security_mode = _render_security_mode_selector()
    sample = build_signed_sample_sequence()
    _render_sample_panel(service, sample, security_mode)
    _render_upload_panel(service, security_mode)

    receipt = st.session_state.get(_RECEIPT_KEY)
    error = st.session_state.get(_ERROR_KEY)
    if isinstance(receipt, IngestionReceipt):
        _render_receipt(receipt)
    elif isinstance(error, str):
        st.error(error, icon=":material/error:")


def _render_sample_panel(
    service: SignedDocumentIngestionService,
    sample: SignedSampleSequence,
    security_mode: DocumentSecurityMode,
) -> None:
    history = service.history(SAMPLE_DOCUMENT_ID)
    has_initial = any(item.revision_number == 1 for item in history)
    has_revised = any(item.revision_number == 2 for item in history)
    st.markdown(
        """
        <section class="sodif-ingestion-sample">
            <div><div class="sodif-card-caption">Exemplu verificabil</div>
            <h2>Construiește un istoric semnat</h2>
            <p>Preia revizia inițială, apoi continuă documentul cu o revizie nouă legată
            criptografic de conținutul deja acceptat.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    initial_action, revision_action, download_action = st.columns(3)
    with initial_action:
        if st.button(
            "Arhivează revizia inițială",
            type="primary",
            icon=":material/archive:",
            use_container_width=True,
        ) and _ingest(
            service,
            sample.initial.content,
            sample.initial.revision,
            sample.initial.original_name,
            security_mode,
        ):
            st.rerun()
    with revision_action:
        if st.button(
            "Arhivează revizia următoare",
            icon=":material/upgrade:",
            disabled=not has_initial,
            use_container_width=True,
        ) and _ingest(
            service,
            sample.revised.content,
            sample.revised.revision,
            sample.revised.original_name,
            security_mode,
        ):
            st.rerun()
    with download_action:
        st.download_button(
            "Descarcă istoricul semnat",
            data=sample.package,
            file_name=SAMPLE_SEQUENCE_ZIP_NAME,
            mime="application/zip",
            icon=":material/download:",
            use_container_width=True,
        )
    if has_revised:
        status = "Istoricul curent are două revizii semnate și legate verificabil."
    elif has_initial:
        status = "Revizia inițială este confirmată. Următoarea revizie poate continua istoricul."
    else:
        status = "Revizia următoare devine disponibilă după acceptarea reviziei inițiale."
    st.markdown(f'<p class="sodif-inline-note">{status}</p>', unsafe_allow_html=True)


def _render_upload_panel(
    service: SignedDocumentIngestionService,
    security_mode: DocumentSecurityMode,
) -> None:
    st.markdown(
        '<div class="sodif-section-label compact">Încarcă o revizie semnată</div>',
        unsafe_allow_html=True,
    )
    document_column, signature_column = st.columns(2)
    with document_column:
        document = st.file_uploader(
            "Document PDF",
            type=["pdf"],
            help="Conținutul trebuie să fie identic cu revizia acoperită de semnătură.",
        )
    with signature_column:
        signature = st.file_uploader(
            "Dovada semnăturii",
            type=["json"],
            help="Fișier JSON care conține metadatele reviziei și semnătura detașată.",
        )
    action, note = st.columns((0.28, 0.72), vertical_alignment="center")
    with action:
        submitted = st.button(
            "Verifică și arhivează",
            type="primary",
            icon=":material/verified_user:",
            disabled=document is None or signature is None,
            use_container_width=True,
        )
    with note:
        st.markdown(
            '<p class="sodif-inline-note">Niciun document nu este păstrat dacă verificarea '
            "eșuează.</p>",
            unsafe_allow_html=True,
        )
    if submitted and document is not None and signature is not None:
        try:
            revision = SignedRevision.model_validate_json(signature.getvalue())
        except (ValidationError, ValueError):
            _set_error("Dovada semnăturii nu are structura acceptată.")
        else:
            _ingest(service, document.getvalue(), revision, document.name, security_mode)


def _render_security_mode_selector() -> DocumentSecurityMode:
    st.markdown(
        '<div class="sodif-section-label compact">Regim de protecție</div>',
        unsafe_allow_html=True,
    )
    selected = st.session_state.get(_ADVANCED_SECURITY_KEY, True)
    enabled = st.checkbox(
        "Activează protecția avansată SODIF pentru acest document",
        value=bool(selected),
        key=_ADVANCED_SECURITY_WIDGET_KEY,
        help=(
            "Aplică verificarea semantică independentă, dovada de invariabilitate și "
            "autorizarea criptografică a acțiunii API."
        ),
    )
    st.session_state[_ADVANCED_SECURITY_KEY] = enabled
    if enabled:
        st.caption(
            "Documentul este clasificat pentru consens semantic, permis criptografic unic "
            "și control la execuția API."
        )
        return DocumentSecurityMode.ADVANCED
    st.caption(
        "Documentul urmează fluxul standard de verificare a semnăturii, integrității, "
        "reviziilor și arhivării."
    )
    return DocumentSecurityMode.STANDARD


def _ingest(
    service: SignedDocumentIngestionService,
    content: bytes,
    revision: SignedRevision,
    original_name: str,
    security_mode: DocumentSecurityMode,
) -> bool:
    try:
        receipt = service.ingest(content, revision, original_name, security_mode)
    except DocumentRejected as exc:
        _set_error(_REJECTION_MESSAGES[exc.code])
        return False
    except ArchiveConflict:
        _set_error(
            "Revizia intră în conflict cu istoricul existent. Regimul de protecție trebuie "
            "să rămână același pentru toate reviziile documentului."
        )
        return False
    except ArchiveError:
        _set_error("Arhiva nu a putut confirma integritatea documentului.")
        return False
    else:
        st.session_state[_RECEIPT_KEY] = receipt
        st.session_state.pop(_ERROR_KEY, None)
        return True


def _set_error(message: str) -> None:
    st.session_state[_ERROR_KEY] = message
    st.session_state.pop(_RECEIPT_KEY, None)


def _render_receipt(receipt: IngestionReceipt) -> None:
    record = receipt.archive
    title = "Revizie deja existentă" if receipt.duplicate else "Document verificat și arhivat"
    detail = (
        "Integritatea a fost reconfirmată; nu a fost creată o copie suplimentară."
        if receipt.duplicate
        else "Semnătura, conținutul și istoricul reviziei au fost confirmate."
    )
    digest = f"{record.content_digest[:25]}…{record.content_digest[-10:]}"
    security_label = _security_mode_label(record.security_mode)
    if record.security_mode is DocumentSecurityMode.ADVANCED:
        security_detail = (
            "Documentul este inclus în regimul avansat de verificare semantică și autorizare "
            "controlată a acțiunii API."
        )
    else:
        security_detail = "Documentul este administrat în regimul standard de integritate."
    st.markdown(
        f"""
        <section class="sodif-ingestion-receipt">
            <div class="sodif-ready-mark" aria-hidden="true"><span></span></div>
            <div><div class="sodif-summary-kicker">Preluare finalizată</div>
            <h2>{escape(title)}</h2><p>{escape(detail)}</p></div>
        </section>
        <section class="sodif-ingestion-metadata">
            <div><small>Document</small><strong>{escape(record.document_id)}</strong></div>
            <div><small>Revizie</small><strong>{record.revision_number}</strong></div>
            <div><small>Semnatar</small><strong>{escape(record.signer_id)}</strong></div>
            <div><small>Regim de securitate</small><strong>{escape(security_label)}</strong></div>
            <div><small>Identificator arhivă</small><code>{escape(record.archive_id)}</code></div>
            <div><small>Amprentă document</small><code>{escape(digest)}</code></div>
        </section>
        <p class="sodif-inline-note">{escape(security_detail)}</p>
        """,
        unsafe_allow_html=True,
    )


def _security_mode_label(mode: DocumentSecurityMode) -> str:
    if mode is DocumentSecurityMode.ADVANCED:
        return "Protecție avansată SODIF"
    return "Protecție standard"
