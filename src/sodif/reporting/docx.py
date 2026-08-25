"""Professional deterministic DOCX assurance report."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from docx import Document
from docx.document import Document as WordDocument
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from sodif.demo.models import FlightKind, FlightReport
from sodif.ui.presentation import FlightView, ScenarioView, present_flight

_NAVY = "0B2545"
_BLUE = "2E74B5"
_DARK_BLUE = "1F4D78"
_TEAL = "087F8C"
_MUTED = "607086"
_LIGHT_FILL = "F2F4F7"
_SUCCESS_FILL = "EAF7F3"
_SUCCESS = "087A64"
_WARNING_FILL = "FFF5DF"
_WARNING = "A8660C"
_DANGER_FILL = "FFF0F1"
_DANGER = "B33B47"
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def render_docx_report(report: FlightReport) -> bytes:
    """Render one report using the standard-business-brief design preset."""
    document = Document()
    _configure_document(document, report)
    view = present_flight(report)
    _add_masthead(document, report, view)
    _add_decision_register(document, view)
    for scenario in view.scenarios:
        _add_scenario(document, scenario)
    buffer = BytesIO()
    document.save(buffer)
    return _normalize_docx(buffer.getvalue())


def _configure_document(document: WordDocument, report: FlightReport) -> None:
    section = document.sections[0]
    section.start_type = WD_SECTION_START.NEW_PAGE
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.right_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)

    properties = document.core_properties
    properties.title = "Raport operațional SODIF"
    properties.subject = "Auditul execuției controlate a intenției semnate"
    properties.author = "SODIF"
    properties.last_modified_by = "SODIF"
    properties.created = report.started_at.replace(tzinfo=None)
    properties.modified = report.completed_at.replace(tzinfo=None)
    properties.revision = 1
    properties.comments = "Generat automat din jurnalul operațional SODIF."

    _configure_styles(document)
    _configure_numbering(document)
    _configure_header(section.header.paragraphs[0])
    _configure_footer(section.footer.paragraphs[0], report.report_id)


def _configure_styles(document: WordDocument) -> None:
    normal = document.styles["Normal"]
    _set_style_font(normal, "Calibri", 11, _NAVY)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.1

    heading_tokens = {
        "Heading 1": (16, _BLUE, 16, 8),
        "Heading 2": (13, _BLUE, 12, 6),
        "Heading 3": (12, _DARK_BLUE, 8, 4),
    }
    for name, (size, color, before, after) in heading_tokens.items():
        style = document.styles[name]
        _set_style_font(style, "Calibri", size, color, bold=True)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    bullet = document.styles["List Bullet"]
    _set_style_font(bullet, "Calibri", 11, _NAVY)
    bullet.paragraph_format.left_indent = Inches(0.5)
    bullet.paragraph_format.first_line_indent = Inches(-0.25)
    bullet.paragraph_format.space_after = Pt(8)
    bullet.paragraph_format.line_spacing = 1.167

    evidence = document.styles.add_style("SODIF Evidence", WD_STYLE_TYPE.PARAGRAPH)
    evidence.base_style = normal
    _set_style_font(evidence, "Consolas", 9, _DARK_BLUE)
    evidence.paragraph_format.left_indent = Inches(0.16)
    evidence.paragraph_format.space_after = Pt(4)
    evidence.paragraph_format.keep_together = True


def _set_style_font(
    style: object,
    name: str,
    size: float,
    color: str,
    *,
    bold: bool | None = None,
) -> None:
    font = style.font  # type: ignore[attr-defined]
    font.name = name
    font.size = Pt(size)
    font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        font.bold = bold
    rpr = style._element.get_or_add_rPr()  # type: ignore[attr-defined]
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    fonts.set(qn("w:ascii"), name)
    fonts.set(qn("w:hAnsi"), name)
    fonts.set(qn("w:eastAsia"), name)


def _configure_numbering(document: WordDocument) -> None:
    numbering = document.part.numbering_part.element
    for level in numbering.iter(qn("w:lvl")):
        number_format = level.find(qn("w:numFmt"))
        if number_format is None or number_format.get(qn("w:val")) != "bullet":
            continue
        properties = level.find(qn("w:pPr"))
        if properties is None:
            properties = OxmlElement("w:pPr")
            level.append(properties)
        indent = properties.find(qn("w:ind"))
        if indent is None:
            indent = OxmlElement("w:ind")
            properties.append(indent)
        indent.set(qn("w:left"), "720")
        indent.set(qn("w:hanging"), "360")
        tabs = properties.find(qn("w:tabs"))
        if tabs is None:
            tabs = OxmlElement("w:tabs")
            properties.insert(0, tabs)
        for child in list(tabs):
            tabs.remove(child)
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "num")
        tab.set(qn("w:pos"), "720")
        tabs.append(tab)


def _configure_header(paragraph: Paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run("SODIF  |  CONTROL TRANZACȚIONAL")
    _set_run_font(run, "Calibri", 8, _MUTED, bold=True)


def _configure_footer(paragraph: Paragraph, report_id: str) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.space_before = Pt(0)
    run = paragraph.add_run(f"{report_id}  |  Page ")
    _set_run_font(run, "Calibri", 8, _MUTED)
    field_run = paragraph.add_run()
    _set_run_font(field_run, "Calibri", 8, _MUTED)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    field_text = OxmlElement("w:t")
    field_text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    field_run._r.extend((begin, instruction, separate, field_text, end))


def _add_masthead(document: WordDocument, report: FlightReport, view: FlightView) -> None:
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(14)

    kicker = document.add_paragraph()
    kicker.paragraph_format.space_after = Pt(6)
    _set_run_font(kicker.add_run("SIGNED INTENT CONTROL"), "Calibri", 9, _TEAL, bold=True)

    flight_title = {
        FlightKind.SECURITY: "RAPORT SECURITY FLIGHT",
        FlightKind.TRANSVERSAL: "RAPORT TRANSVERSAL FLIGHT",
    }[report.flight_kind]
    title = document.add_paragraph()
    title.paragraph_format.space_after = Pt(4)
    title.paragraph_format.keep_with_next = True
    _set_run_font(title.add_run(flight_title), "Calibri", 24, _NAVY, bold=True)

    subtitle = document.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(18)
    subtitle.paragraph_format.keep_with_next = True
    _set_run_font(
        subtitle.add_run(
            "Raport Document-to-API pentru execuția controlată a unei comenzi de achiziție"
        ),
        "Calibri",
        12,
        _MUTED,
    )

    metadata = (
        ("Organizație", report.configuration.organization_name),
        ("Spațiu operațional", report.configuration.workspace_name),
        ("Domeniu", report.configuration.domain_name),
        ("Mediu", report.configuration.environment),
        ("Raport", report.report_id),
        ("Rezultat", "CONFORM" if report.passed else "NECONFORM"),
        ("Sigilat la", report.completed_at.isoformat().replace("+00:00", "Z")),
        (
            "Domeniu",
            "Comandă semnată / API operațional"
            if report.flight_kind is FlightKind.SECURITY
            else "Comandă semnată / arhivă verificabilă / Gateway semantic / API operațional",
        ),
        (
            "Serviciu protejat",
            f"{report.configuration.protected_service} · {report.configuration.route_id}",
        ),
    )
    for label, value in metadata:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)
        _set_run_font(paragraph.add_run(f"{label}: "), "Calibri", 10, _NAVY, bold=True)
        _set_run_font(paragraph.add_run(value), "Calibri", 10, _NAVY)

    document.add_paragraph().paragraph_format.space_after = Pt(4)
    _add_callout(document, view.title, view.detail, "success" if report.passed else "danger")


def _add_callout(
    document: WordDocument,
    title: str,
    detail: str,
    tone: str,
) -> None:
    fill, accent = {
        "success": (_SUCCESS_FILL, _SUCCESS),
        "warning": (_WARNING_FILL, _WARNING),
        "danger": (_DANGER_FILL, _DANGER),
    }[tone]
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.12)
    paragraph.paragraph_format.right_indent = Inches(0.08)
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(10)
    paragraph.paragraph_format.keep_together = True
    properties = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "7")
    left.set(qn("w:color"), accent)
    borders.append(left)
    properties.append(borders)
    _set_run_font(paragraph.add_run(f"{title}\n"), "Calibri", 11, accent, bold=True)
    _set_run_font(paragraph.add_run(detail), "Calibri", 10.5, _NAVY)


def _add_decision_register(document: WordDocument, view: FlightView) -> None:
    document.add_heading("Registrul deciziilor", level=1)
    paragraph = document.add_paragraph(
        "Registrul sintetizează decizia observabilă și comportamentul rezultat al API-ului."
    )
    paragraph.paragraph_format.keep_with_next = True
    table = document.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    widths = (3450, 1950, 3960)
    _set_table_geometry(table, widths)
    headers = ("Situație", "Decizie", "Efect asupra API")
    for cell, text in zip(table.rows[0].cells, headers, strict=True):
        _set_cell_text(cell, text, bold=True, color=_NAVY, size=9.5)
        _set_cell_fill(cell, _LIGHT_FILL)
    _repeat_table_header(table)
    for scenario in view.scenarios:
        cells = table.add_row().cells
        _apply_row_geometry(cells, widths)
        _set_cell_text(cells[0], scenario.title, size=9.5)
        _set_cell_text(
            cells[1],
            scenario.verdict,
            bold=True,
            color=_tone_color(scenario.tone),
            size=9.5,
        )
        _set_cell_text(cells[2], scenario.api_effect, size=9.5)
    note = document.add_paragraph(
        "Pachetul de audit include reprezentarea structurată a raportului, jurnalul ordonat "
        "ordonat și manifestul de integritate care permit verificarea acestor concluzii."
    )
    note.paragraph_format.space_before = Pt(8)


def _add_scenario(document: WordDocument, scenario: ScenarioView) -> None:
    kicker = document.add_paragraph()
    kicker.paragraph_format.page_break_before = True
    kicker.paragraph_format.space_after = Pt(3)
    _set_run_font(kicker.add_run(scenario.kicker.upper()), "Calibri", 8.5, _TEAL, bold=True)
    document.add_heading(scenario.title, level=1)
    document.add_paragraph(scenario.summary)
    _add_callout(document, f"Decizie: {scenario.verdict}", scenario.verdict_detail, scenario.tone)

    document.add_heading("Rezultatul controalelor", level=2)
    for control in scenario.controls:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.keep_together = True
        _set_run_font(
            paragraph.add_run(f"{control.name} — {control.state}. "),
            "Calibri",
            11,
            _tone_color(control.tone),
            bold=True,
        )
        _set_run_font(paragraph.add_run(control.detail), "Calibri", 11, _NAVY)

    document.add_heading("Rațiunea deciziei și efectul asupra API", level=2)
    paragraph = document.add_paragraph()
    _set_run_font(paragraph.add_run("Rațiune. "), "Calibri", 11, _NAVY, bold=True)
    _set_run_font(paragraph.add_run(scenario.optimization_note), "Calibri", 11, _NAVY)
    paragraph = document.add_paragraph()
    _set_run_font(paragraph.add_run(f"{scenario.api_effect}. "), "Calibri", 11, _NAVY, bold=True)
    _set_run_font(paragraph.add_run(scenario.api_detail), "Calibri", 11, _NAVY)

    document.add_heading("Traseul deciziei", level=2)
    for timeline_item in scenario.timeline:
        document.add_paragraph(timeline_item, style="List Bullet")

    document.add_heading("Identificatori și trasabilitate", level=2)
    for evidence in scenario.evidence:
        paragraph = document.add_paragraph(style="SODIF Evidence")
        _set_run_font(
            paragraph.add_run(f"{evidence.label}: "),
            "Consolas",
            9,
            _MUTED,
            bold=True,
        )
        _set_run_font(paragraph.add_run(evidence.value), "Consolas", 9, _DARK_BLUE)


def _set_run_font(
    run: Run,
    name: str,
    size: float,
    color: str,
    *,
    bold: bool | None = None,
) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    fonts.set(qn("w:ascii"), name)
    fonts.set(qn("w:hAnsi"), name)
    fonts.set(qn("w:eastAsia"), name)


def _tone_color(tone: str) -> str:
    return {
        "success": _SUCCESS,
        "warning": _WARNING,
        "danger": _DANGER,
        "neutral": _MUTED,
    }[tone]


def _set_table_geometry(table: Table, widths: tuple[int, ...]) -> None:
    if sum(widths) != 9360:
        raise ValueError("report table widths must total 9360 DXA")
    table.autofit = False
    properties = table._tbl.tblPr
    _replace_sized_element(properties, "w:tblW", "9360", type_value="dxa")
    _replace_sized_element(properties, "w:tblInd", "120", type_value="dxa")
    layout = properties.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        properties.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        column = OxmlElement("w:gridCol")
        column.set(qn("w:w"), str(width))
        grid.append(column)
    for row in table.rows:
        _apply_row_geometry(row.cells, widths)


def _apply_row_geometry(cells: tuple[_Cell, ...], widths: tuple[int, ...]) -> None:
    for cell, width in zip(cells, widths, strict=True):
        cell.width = Inches(width / 1440)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        properties = cell._tc.get_or_add_tcPr()
        tc_width = properties.get_or_add_tcW()
        tc_width.set(qn("w:type"), "dxa")
        tc_width.set(qn("w:w"), str(width))
        margins = properties.find(qn("w:tcMar"))
        if margins is None:
            margins = OxmlElement("w:tcMar")
            properties.append(margins)
        for edge, value in (("top", 80), ("bottom", 80), ("start", 120), ("end", 120)):
            item = margins.find(qn(f"w:{edge}"))
            if item is None:
                item = OxmlElement(f"w:{edge}")
                margins.append(item)
            item.set(qn("w:w"), str(value))
            item.set(qn("w:type"), "dxa")


def _replace_sized_element(
    parent: object,
    tag: str,
    value: str,
    *,
    type_value: str,
) -> None:
    element = parent.find(qn(tag))  # type: ignore[attr-defined]
    if element is None:
        element = OxmlElement(tag)
        parent.append(element)  # type: ignore[attr-defined]
    element.set(qn("w:w"), value)
    element.set(qn("w:type"), type_value)


def _set_cell_text(
    cell: _Cell,
    text: str,
    *,
    bold: bool = False,
    color: str = _NAVY,
    size: float = 10,
) -> None:
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.05
    _set_run_font(paragraph.add_run(text), "Calibri", size, color, bold=bold)


def _set_cell_fill(cell: _Cell, color: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shading)


def _repeat_table_header(table: Table) -> None:
    properties = table.rows[0]._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    properties.append(marker)


def _normalize_docx(data: bytes) -> bytes:
    source = BytesIO(data)
    output = BytesIO()
    with (
        ZipFile(source, "r") as reader,
        ZipFile(
            output,
            "w",
            compression=ZIP_DEFLATED,
            compresslevel=9,
        ) as writer,
    ):
        for original in sorted(reader.infolist(), key=lambda item: item.filename):
            if original.is_dir():
                continue
            info = ZipInfo(original.filename, date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o600 << 16
            writer.writestr(
                info,
                reader.read(original.filename),
                compress_type=ZIP_DEFLATED,
                compresslevel=9,
            )
    return output.getvalue()
