"""Generate the Complete Project PDF for capstone submission.

Per the Project Guidelines: "add to the Project Overview Doc by merging all
submission materials (notebooks, code, etc.) into a single Complete Project
PDF. Do not include large data files or screenshots."

So this renders, in order:
  1. The Project Overview Doc (markdown -> PDF)
  2. All source code (src/, scripts/, requirements.txt, .env.example)

into one PDF. Run from repo root:

    python scripts/generate_code_pdf.py
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Preformatted,
    PageBreak,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)
from reportlab.lib import colors

REPO_ROOT = Path(__file__).resolve().parent.parent
OVERVIEW_DOC_PATH = REPO_ROOT / "docs" / "project submission" / "overview" / "PROJECT_OVERVIEW_DOC.md"
OUTPUT_PATH = REPO_ROOT / "docs" / "project submission" / "Jobs_Pipeline_Complete_Project_PDF.pdf"

INCLUDE_DIRS = ["src", "scripts"]
INCLUDE_TOP_LEVEL_FILES = [
    "requirements.txt",
    ".env.example",
]
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_DIR_NAMES = {"__pycache__", ".git"}


def collect_files() -> list[Path]:
    files: list[Path] = []
    for d in INCLUDE_DIRS:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for root, dirs, filenames in os.walk(base):
            dirs[:] = [x for x in dirs if x not in EXCLUDE_DIR_NAMES]
            for fname in sorted(filenames):
                p = Path(root) / fname
                if p.suffix in EXCLUDE_SUFFIXES:
                    continue
                files.append(p)
    for f in INCLUDE_TOP_LEVEL_FILES:
        p = REPO_ROOT / f
        if p.exists():
            files.append(p)
    return sorted(files, key=lambda p: str(p.relative_to(REPO_ROOT)))


# ---------------------------------------------------------------------------
# Minimal markdown -> reportlab renderer (headings, bold/italic/code spans,
# bullet lists, tables, fenced code blocks, hr, plain paragraphs). Covers
# exactly the subset of markdown used in the Overview Doc, not full CommonMark.
# ---------------------------------------------------------------------------

def inline_to_html(text: str) -> str:
    text = text.replace("—", "--").replace("–", "-")
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def build_overview_flowables(md_text: str, styles: dict) -> list:
    lines = md_text.split("\n")
    story = []
    i = 0
    n = len(lines)
    bullet_buffer: list[str] = []

    def flush_bullets():
        if bullet_buffer:
            items = [ListItem(Paragraph(inline_to_html(b), styles["body"]), leftIndent=12) for b in bullet_buffer]
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=18))
            bullet_buffer.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            flush_bullets()
            i += 1
            continue

        if stripped == "---":
            flush_bullets()
            story.append(Spacer(1, 0.08 * inch))
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_bullets()
            level = len(heading_match.group(1))
            text = inline_to_html(heading_match.group(2))
            style_key = f"h{min(level, 3)}"
            story.append(Spacer(1, 0.12 * inch))
            story.append(Paragraph(text, styles[style_key]))
            i += 1
            continue

        if stripped.startswith("```"):
            flush_bullets()
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            story.append(Preformatted("\n".join(code_lines), styles["code"]))
            story.append(Spacer(1, 0.08 * inch))
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            flush_bullets()
            table_rows = []
            header = [c.strip() for c in stripped.strip("|").split("|")]
            table_rows.append(header)
            i += 2  # skip header + separator
            while i < n and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                table_rows.append(row)
                i += 1
            wrapped = [
                [Paragraph(inline_to_html(cell), styles["table_cell"]) for cell in row]
                for row in table_rows
            ]
            t = Table(wrapped, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.1 * inch))
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet_match:
            bullet_buffer.append(bullet_match.group(1))
            i += 1
            continue

        # Plain paragraph: accumulate until blank line / next block marker.
        flush_bullets()
        para_lines = [stripped]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(r"^(#{1,6}\s|```|[-*]\s|\|)", lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        story.append(Paragraph(inline_to_html(" ".join(para_lines)), styles["body"]))
        story.append(Spacer(1, 0.06 * inch))

    flush_bullets()
    return story


def build_overview_styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("MDH1", parent=base["Heading1"], fontSize=16, spaceAfter=8),
        "h2": ParagraphStyle("MDH2", parent=base["Heading2"], fontSize=13, spaceAfter=6, textColor=colors.HexColor("#1a1a1a")),
        "h3": ParagraphStyle("MDH3", parent=base["Heading3"], fontSize=11, spaceAfter=4),
        "body": ParagraphStyle("MDBody", parent=base["Normal"], fontSize=9.5, leading=13, spaceAfter=2),
        "table_cell": ParagraphStyle("MDTableCell", parent=base["Normal"], fontSize=8, leading=10),
        "code": ParagraphStyle("MDCode", fontName="Courier", fontSize=7.5, leading=9),
    }


# ---------------------------------------------------------------------------
# Code section
# ---------------------------------------------------------------------------

def build_code_flowables(files: list[Path], styles: dict) -> tuple[list, int]:
    story = []
    story.append(PageBreak())
    story.append(Paragraph("Complete Project Code", styles["h1"]))
    story.append(Paragraph(
        "All source code (src/, scripts/, requirements.txt, .env.example). "
        "Data files, logs, and screenshots excluded per submission guidelines.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Contents", styles["h2"]))
    for f in files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        story.append(Paragraph(escape(rel), styles["body"]))
    story.append(PageBreak())

    total_lines = 0
    for f in files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        story.append(Paragraph(escape(rel), styles["h2"]))
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"<could not read file: {e}>"
        total_lines += text.count("\n") + 1
        story.append(Preformatted(text, styles["code"]))
        story.append(PageBreak())

    return story, total_lines


def build_pdf(files: list[Path]) -> None:
    styles = build_overview_styles()

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=LETTER,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title="Jobs Pipeline - Complete Project PDF",
        author="the author",
    )

    story = []
    overview_md = OVERVIEW_DOC_PATH.read_text(encoding="utf-8")
    story.extend(build_overview_flowables(overview_md, styles))

    code_story, total_lines = build_code_flowables(files, styles)
    story.extend(code_story)

    doc.build(story)
    print(f"Wrote {OUTPUT_PATH} ({len(files)} code files, ~{total_lines} code lines, "
          f"overview doc: {OVERVIEW_DOC_PATH.name})")


if __name__ == "__main__":
    files = collect_files()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(files)
