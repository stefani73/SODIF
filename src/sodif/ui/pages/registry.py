"""Professional document registry and revision viewer."""

from datetime import datetime
from html import escape

import streamlit as st

from sodif.archive import (
    ArchiveError,
    ArchiveQuery,
    ArchiveRecord,
    ArchiveSummary,
    DocumentRegistryService,
    RegistrySelection,
)
from sodif.ui.pages.shared import render_page_intro

_SELECTED_ARCHIVE_KEY = "sodif_registry_selected_archive"


def render_document_registry(
    service: DocumentRegistryService,
    ingestion_page: str,
) -> None:
    """Render archive overview, bounded search, revision history and PDF preview."""
    render_page_intro(
        "Documente",
        "Registru documente",
        "Consultă documentele acceptate, urmărește fiecare revizie și deschide conținutul "
        "numai după reconfirmarea integrității din arhivă.",
    )
    summary = service.summary()
    _render_summary(summary)
    if summary.total_revisions == 0:
        _render_empty_archive(ingestion_page)
        return

    query = _render_filters(summary)
    page = service.search(query)
    records = _latest_document_records(page.records)
    if not records:
        _render_no_results()
        return

    selected_archive_id = _selected_archive(records)
    results_column, detail_column = st.columns((0.37, 0.63), gap="large")
    with results_column:
        _render_results(records, page.total, selected_archive_id)

    selected_archive_id = _selected_archive(records)
    try:
        selection = service.open(selected_archive_id)
    except ArchiveError:
        with detail_column:
            st.error(
                "Documentul nu poate fi deschis deoarece arhiva nu i-a confirmat integritatea.",
                icon=":material/error:",
            )
        return
    with detail_column:
        _render_selection(service, selection)


def _render_summary(summary: ArchiveSummary) -> None:
    cards = (
        ("Documente", str(summary.total_documents), "identități distincte"),
        ("Revizii", str(summary.total_revisions), "înregistrări verificabile"),
        ("Semnatari", str(len(summary.signer_ids)), "identități de încredere"),
        ("Volum", _format_size(summary.total_bytes), "conținut arhivat"),
    )
    columns = st.columns(4)
    for column, (label, value, detail) in zip(columns, cards, strict=True):
        with column:
            st.markdown(
                f'<article class="sodif-registry-stat"><small>{escape(label)}</small>'
                f"<strong>{escape(value)}</strong><span>{escape(detail)}</span></article>",
                unsafe_allow_html=True,
            )


def _render_filters(summary: ArchiveSummary) -> ArchiveQuery:
    st.markdown(
        '<div class="sodif-section-label compact">Caută în registru</div>',
        unsafe_allow_html=True,
    )
    search_column, signer_column = st.columns((0.68, 0.32))
    with search_column:
        text = st.text_input(
            "Document, fișier sau semnatar",
            placeholder="Ex.: comandă, doc-ingestion sau flight-signer",
        )
    with signer_column:
        signer_id = st.selectbox(
            "Semnatar",
            ("", *summary.signer_ids),
            format_func=_signer_label,
        )
    return ArchiveQuery(text=text.strip(), signer_id=signer_id or None, limit=100)


def _render_results(
    records: tuple[ArchiveRecord, ...],
    matching_revisions: int,
    selected_archive_id: str,
) -> None:
    document_count = _count_label(len(records), "document", "documente")
    revision_count = _count_label(matching_revisions, "revizie găsită", "revizii găsite")
    st.markdown(
        f'<div class="sodif-registry-results-head"><strong>{document_count}</strong>'
        f"<span>{revision_count}</span></div>",
        unsafe_allow_html=True,
    )
    for record in records:
        tone = " active" if record.archive_id == selected_archive_id else ""
        st.markdown(
            f"""
            <article class="sodif-registry-record{tone}">
                <div><span>PDF</span><small>Revizia {record.revision_number}</small></div>
                <h3>{escape(record.original_name)}</h3>
                <p>{escape(record.document_id)}</p>
                <footer><span>{escape(record.signer_id)}</span>
                <time>{escape(_format_datetime(record.archived_at))}</time></footer>
            </article>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Deschide documentul",
            key=f"registry-open-{record.archive_id}",
            icon=":material/visibility:",
            use_container_width=True,
        ):
            st.session_state[_SELECTED_ARCHIVE_KEY] = record.archive_id


def _render_selection(
    service: DocumentRegistryService,
    selection: RegistrySelection,
) -> None:
    record = selection.document.record
    labels = {
        item.archive_id: f"Revizia {item.revision_number} · {_format_datetime(item.signed_at)}"
        for item in selection.history
    }
    revision_ids = tuple(labels)
    selected_id = st.selectbox(
        "Revizia vizualizată",
        revision_ids,
        index=revision_ids.index(record.archive_id),
        format_func=labels.__getitem__,
    )
    if selected_id != record.archive_id:
        st.session_state[_SELECTED_ARCHIVE_KEY] = selected_id
        try:
            selection = service.open(selected_id)
        except ArchiveError:
            st.error(
                "Revizia selectată nu poate fi deschisă în condiții de integritate.",
                icon=":material/error:",
            )
            return
        record = selection.document.record

    title_column, download_column = st.columns((0.7, 0.3), vertical_alignment="bottom")
    with title_column:
        st.markdown(
            f"""
            <section class="sodif-registry-detail-head">
                <div class="sodif-assurance-label"><span></span>Integritate reconfirmată</div>
                <h2>{escape(record.original_name)}</h2>
                <p>{escape(record.document_id)} · Revizia {record.revision_number}</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with download_column:
        st.download_button(
            "Descarcă revizia",
            data=selection.document.content,
            file_name=record.original_name,
            mime=record.media_type,
            icon=":material/download:",
            use_container_width=True,
        )

    _render_metadata(record)
    document_tab, traceability_tab = st.tabs(("Document", "Trasabilitate"))
    with document_tab:
        st.markdown(
            '<div class="sodif-preview-label">Previzualizare securizată</div>',
            unsafe_allow_html=True,
        )
        st.pdf(selection.document.content, height=540, key=f"registry-pdf-{record.archive_id}")
    with traceability_tab:
        _render_traceability(record, selection.history)


def _render_metadata(record: ArchiveRecord) -> None:
    digest = f"{record.content_digest[:22]}…{record.content_digest[-10:]}"
    st.markdown(
        f"""
        <section class="sodif-registry-metadata">
            <div><small>Semnatar</small><strong>{escape(record.signer_id)}</strong></div>
            <div><small>Semnat</small><strong>{escape(_format_datetime(record.signed_at))}</strong></div>
            <div><small>Dimensiune</small><strong>{escape(_format_size(record.size_bytes))}</strong></div>
            <div><small>Amprentă</small><code>{escape(digest)}</code></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_traceability(
    selected: ArchiveRecord,
    history: tuple[ArchiveRecord, ...],
) -> None:
    revision_count = _count_label(len(history), "revizie", "revizii")
    items = "".join(
        _history_item(item, item.archive_id == selected.archive_id) for item in reversed(history)
    )
    st.markdown(
        f"""
        <div class="sodif-traceability-intro"><strong>Lanț de revizii verificat</strong>
        <span>{revision_count}, fără întreruperi sau ramificații</span></div>
        <section class="sodif-revision-history">{items}</section>
        """,
        unsafe_allow_html=True,
    )


def _history_item(record: ArchiveRecord, active: bool) -> str:
    tone = " active" if active else ""
    predecessor = (
        "Revizie inițială"
        if record.previous_revision_digest is None
        else f"Continuă {record.previous_revision_digest[:18]}…"
    )
    return (
        f'<article class="sodif-revision-item{tone}"><span></span><div>'
        f"<strong>Revizia {record.revision_number}</strong><small>{escape(predecessor)}</small>"
        f"</div><time>{escape(_format_datetime(record.accepted_at))}</time></article>"
    )


def _render_empty_archive(ingestion_page: str) -> None:
    st.markdown(
        """
        <section class="sodif-empty-panel">
            <div class="sodif-ready-mark" aria-hidden="true"><span></span></div>
            <div><h2>Registrul este pregătit</h2>
            <p>Preia primul document semnat pentru a iniția istoricul verificabil.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(
        ingestion_page,
        label="Preia un document",
        icon=":material/upload_file:",
    )


def _render_no_results() -> None:
    st.info(
        "Nu există documente care corespund criteriilor selectate.",
        icon=":material/search_off:",
    )


def _latest_document_records(records: tuple[ArchiveRecord, ...]) -> tuple[ArchiveRecord, ...]:
    latest: dict[str, ArchiveRecord] = {}
    for record in records:
        current = latest.get(record.document_id)
        if current is None or record.revision_number > current.revision_number:
            latest[record.document_id] = record
    return tuple(
        sorted(
            latest.values(),
            key=lambda item: (item.archived_at, item.document_id),
            reverse=True,
        )
    )


def _selected_archive(records: tuple[ArchiveRecord, ...]) -> str:
    available = {record.archive_id for record in records}
    selected = st.session_state.get(_SELECTED_ARCHIVE_KEY)
    if not isinstance(selected, str) or selected not in available:
        selected = records[0].archive_id
        st.session_state[_SELECTED_ARCHIVE_KEY] = selected
    return selected


def _signer_label(value: str) -> str:
    return value if value else "Toți semnatarii"


def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%d.%m.%Y · %H:%M")


def _format_size(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def _count_label(value: int, singular: str, plural: str) -> str:
    return f"{value} {singular if value == 1 else plural}"
