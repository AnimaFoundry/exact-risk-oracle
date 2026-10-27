#!/usr/bin/env python3
"""Build the local manuscript from a deliberately small Markdown subset.

Original implementation, SPDX-License-Identifier: MIT.
No network, HTML interpretation, embedded commands, or external resource loads.
Fonts: ReportLab 4.4.9 distribution, reportlab/fonts/Vera*.ttf; the accompanying
reportlab/fonts/bitstream-vera-license.txt is copied unchanged to FONT-LICENSE.txt.
The font files themselves are loaded from the installed distribution and subset
embedded in the PDF; they are not copied into this source package.
"""

from __future__ import annotations

import argparse
from functools import partial
from html import escape
from pathlib import Path
import re
import textwrap

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    LongTable,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 48
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN
FONT_PREFIX = "AuditVera"
DASHES = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-",
                       "\u2013": "-", "\u2014": "-", "\u2212": "-",
                       "\u00a0": " ", "\u202f": " "})


def register_fonts() -> None:
    """Load only named local package fonts, never manuscript-provided paths."""
    directory = Path(reportlab.__file__).resolve().parent / "fonts"
    font_files = {
        FONT_PREFIX: "Vera.ttf",
        FONT_PREFIX + "Bold": "VeraBd.ttf",
        FONT_PREFIX + "Italic": "VeraIt.ttf",
        FONT_PREFIX + "BoldItalic": "VeraBI.ttf",
    }
    for name, filename in font_files.items():
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required installed ReportLab font missing: {filename}")
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        FONT_PREFIX,
        normal=FONT_PREFIX,
        bold=FONT_PREFIX + "Bold",
        italic=FONT_PREFIX + "Italic",
        boldItalic=FONT_PREFIX + "BoldItalic",
    )


def safe_text(text: str) -> str:
    """Escape all manuscript markup; only our fixed emphasis tags are emitted."""
    escaped = escape(text.translate(DASHES), quote=True)
    # Delimiters contain text only: raw HTML was escaped before these operations.
    escaped = re.sub(r"`([^`\n]+)`", r'<font name="Courier">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*\n]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", escaped)
    return escaped


def styles() -> dict[str, ParagraphStyle]:
    body = ParagraphStyle(
        "Body", fontName=FONT_PREFIX, fontSize=9.8, leading=13.5,
        textColor=colors.HexColor("#171717"), alignment=TA_LEFT,
        spaceAfter=6.5, splitLongWords=1, allowWidows=0, allowOrphans=0,
    )
    return {
        "body": body,
        "title": ParagraphStyle(
            "Title", parent=body, fontName=FONT_PREFIX + "Bold", fontSize=17,
            leading=21, spaceAfter=12, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Section", parent=body, fontName=FONT_PREFIX + "Bold", fontSize=11.3,
            leading=14.5, spaceBefore=10, spaceAfter=5, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Subsection", parent=body, fontName=FONT_PREFIX + "Bold", fontSize=10.1,
            leading=13.5, spaceBefore=7, spaceAfter=4, keepWithNext=True,
        ),
        "meta": ParagraphStyle(
            "Metadata", parent=body, fontSize=8.8, leading=11.8,
            textColor=colors.HexColor("#404040"), spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=body, leftIndent=11, firstLineIndent=-8,
            spaceAfter=4.5,
        ),
        "reference": ParagraphStyle(
            "Reference", parent=body, fontSize=8.8, leading=12,
            leftIndent=17, firstLineIndent=-17, spaceAfter=5,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=body, fontSize=8.5, leading=11.1,
            spaceBefore=0, spaceAfter=0, allowWidows=1, allowOrphans=1,
        ),
        "header_cell": ParagraphStyle(
            "HeaderCell", parent=body, fontName=FONT_PREFIX + "Bold",
            fontSize=8.5, leading=11.1, spaceBefore=0, spaceAfter=0,
            allowWidows=1, allowOrphans=1,
        ),
        "code": ParagraphStyle(
            "Equation", fontName="Courier", fontSize=8.4, leading=11.3,
            leftIndent=8, rightIndent=8, spaceBefore=3, spaceAfter=8,
            textColor=colors.HexColor("#171717"),
        ),
    }


def table_cells(line: str) -> list[str]:
    """Split a pipe row with escaped literal pipes; no nested Markdown parsing."""
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|") and not content.endswith("\\|"):
        content = content[:-1]
    return [cell.strip().replace("\\|", "|")
            for cell in re.split(r"(?<!\\)\|", content)]


def separator_row(line: str) -> bool:
    cells = table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def make_table(rows: list[list[str]], style: dict[str, ParagraphStyle]) -> LongTable:
    count = len(rows[0])
    if not 1 <= count <= 8:
        raise ValueError("Tables must have one to eight columns; split wider tables.")
    if any(len(row) != count for row in rows):
        raise ValueError("Markdown table has inconsistent column counts.")
    # Allocate a bounded share to verbose columns. Paragraphs wrap long words and
    # URLs inside their exact column width instead of overflowing the page edge.
    weights = []
    for column in range(count):
        lengths = sorted(min(len(row[column]), 90) for row in rows)
        typical = lengths[(3 * (len(lengths) - 1)) // 4]
        weights.append(max(8, min(28, typical ** 0.7)))
    widths = [TEXT_WIDTH * weight / sum(weights) for weight in weights]
    cells = [[Paragraph(safe_text(cell), style["header_cell" if row_index == 0 else "cell"])
              for cell in row] for row_index, row in enumerate(rows)]
    table = LongTable(
        cells, colWidths=widths, repeatRows=1, hAlign="LEFT",
        splitByRow=1, splitInRow=1, spaceBefore=4, spaceAfter=9,
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("LINEABOVE", (0, 0), (-1, 0), 0.65, colors.HexColor("#555555")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.45, colors.HexColor("#777777")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.22, colors.HexColor("#cccccc")),
    ]))
    return table


def equation_block(lines: list[str], style: ParagraphStyle) -> Preformatted:
    text = "\n".join(lines).translate(DASHES)
    if any(ord(character) > 126 for character in text):
        raise ValueError("Equation fences require ASCII notation for reliable monospace rendering.")
    max_columns = int((TEXT_WIDTH - 16) / pdfmetrics.stringWidth("M", "Courier", style.fontSize))
    wrapped = []
    for line in text.splitlines():
        chunks = textwrap.wrap(
            line.expandtabs(4), width=max_columns,
            subsequent_indent="    ", replace_whitespace=False,
            drop_whitespace=False, break_long_words=True, break_on_hyphens=False,
        )
        wrapped.extend(chunks or [""])
    return Preformatted("\n".join(wrapped), style, dedent=0)


def parse_markdown(source: str) -> tuple[str, list]:
    style = styles()
    lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    story = []
    title = None
    references = False
    before_section = True
    index = 0

    def boundary(position: int) -> bool:
        line = lines[position].strip()
        return (not line or line.startswith(("# ", "## ", "### ", "```", "- ", "* "))
                or bool(re.match(r"\d+\.\s", line))
                or (position + 1 < len(lines) and "|" in line
                    and separator_row(lines[position + 1])))

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("```"):
            block = []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                block.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError("Unclosed fenced equation block.")
            story.append(equation_block(block, style["code"]))
            index += 1
            continue
        if line.startswith("# "):
            if title is not None:
                raise ValueError("Exactly one level-one manuscript title is supported.")
            title = line[2:].strip().translate(DASHES)
            story.append(Paragraph(safe_text(title), style["title"]))
            index += 1
            continue
        if line.startswith(("## ", "### ")):
            before_section = False
            level = "h3" if line.startswith("### ") else "h2"
            heading = line.split(" ", 1)[1]
            references = bool(re.search(r"\breferences\b", heading, re.IGNORECASE))
            story.append(Paragraph(safe_text(heading), style[level]))
            index += 1
            continue
        if index + 1 < len(lines) and "|" in line and separator_row(lines[index + 1]):
            rows = [table_cells(line)]
            index += 2
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                rows.append(table_cells(lines[index]))
                index += 1
            story.append(make_table(rows, style))
            continue
        bullet = re.match(r"(?:[-*]\s+|\d+\.\s+)(.*)", line)
        if bullet:
            marker = line.split(" ", 1)[0] if line[0].isdigit() else "-"
            text = bullet.group(1)
            index += 1
            while index < len(lines) and lines[index].startswith("  ") and not boundary(index):
                text += " " + lines[index].strip()
                index += 1
            story.append(Paragraph(safe_text(marker + " " + text), style["bullet"]))
            continue
        paragraph = [line]
        index += 1
        while index < len(lines) and not boundary(index):
            paragraph.append(lines[index].strip())
            index += 1
        text = " ".join(paragraph)
        selected = "reference" if references else "meta" if before_section else "body"
        story.append(Paragraph(safe_text(text), style[selected]))
    if title is None:
        raise ValueError("The manuscript must contain a # title.")
    if not story:
        raise ValueError("Empty manuscript.")
    return title, story


def page_footer(canvas: Canvas, document: BaseDocTemplate) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#b0b0b0"))
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, 35, PAGE_WIDTH - MARGIN, 35)
    canvas.setFont(FONT_PREFIX, 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(MARGIN, 23, "Research manuscript | AnimaFoundry")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 23, str(document.page))
    canvas.restoreState()


def build(source_path: Path, destination: Path) -> Path:
    register_fonts()
    source = source_path.read_text(encoding="utf-8")
    title, story = parse_markdown(source)
    if not (ROOT / "FONT-LICENSE.txt").is_file():
        raise FileNotFoundError("FONT-LICENSE.txt must accompany the embedded-font document.")
    if destination.resolve() == source_path.resolve():
        raise ValueError("PDF output must not overwrite its Markdown input.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = BaseDocTemplate(
        str(destination), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN, title=title, author="AnimaFoundry",
        subject="Exact risk certificates: specialized method, proof and finite validation.",
        creator="exact_risk_oracle/build_paper.py; ReportLab",
        pageCompression=1, allowSplitting=1, invariant=1,
    )
    frame = Frame(
        MARGIN, MARGIN, TEXT_WIDTH, PAGE_HEIGHT - 2 * MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    document.addPageTemplates(PageTemplate(id="Academic", frames=[frame], onPage=page_footer))
    document.build(story, canvasmaker=partial(Canvas, invariant=1))
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "paper.md")
    parser.add_argument("--output", type=Path, default=ROOT / "paper.pdf")
    arguments = parser.parse_args()
    result = build(arguments.source, arguments.output)
    print(result)


if __name__ == "__main__":
    main()
