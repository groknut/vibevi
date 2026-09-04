"""PDF and DOCX document parsers.

PDF rendering uses PyMuPDF to convert pages to images.
DOCX parsing uses python-docx to produce rich HTML.
"""

import os
import tempfile
from typing import TypedDict
from ._meta import FileMeta, file_meta


class PdfPageImage(TypedDict):
    """Single rendered PDF page.

    Attributes:
        page: 1-based page number.
        image_path: Path to the rendered PNG image.
    """
    page: int
    image_path: str


class PdfResult(FileMeta):
    """Parsed PDF file metadata.

    Attributes:
        type: Always "pdf".
        content: Empty string (images used for display).
        pages: Total page count.
        page_images: List of rendered page images.
    """
    type: str
    content: str
    pages: int
    page_images: list[PdfPageImage]


class DocxResult(FileMeta):
    """Parsed DOCX file metadata.

    Attributes:
        type: Always "docx".
        content: Rich HTML representation of the document.
        paragraphs: Number of paragraphs in the document.
    """
    type: str
    content: str
    paragraphs: int


def _escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Raw text.

    Returns:
        HTML-safe string with escaped &, <, >.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_pdf(path: str) -> PdfResult:
    """Parse a PDF file using PyMuPDF, rendering pages as images.

    Each page is rendered at 200 DPI and saved as a PNG in a temp directory.

    Args:
        path: Path to the PDF file.

    Returns:
        PdfResult with page count and image paths.
    """
    try:
        import pymupdf
    except ImportError:
        return {"type": "pdf", "content": "[pymupdf not installed]", "pages": 0, "page_images": [], **file_meta(path)}

    doc = pymupdf.open(path)
    page_images: list[PdfPageImage] = []

    tmp_dir = tempfile.mkdtemp(prefix="vibevi_pdf_")

    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=200)
        image_path = os.path.join(tmp_dir, f"page_{i + 1}.png")
        pix.save(image_path)
        page_images.append({"page": i + 1, "image_path": image_path})

    doc.close()

    return {
        "type": "pdf",
        "content": "",
        "pages": len(page_images),
        "page_images": page_images,
        **file_meta(path),
    }


def _run_to_html(run) -> str:
    """Convert a single Run to an HTML span with inline styles.

    Preserves bold, italic, underline, font size, color, and font name.

    Args:
        run: A python-docx Run object.

    Returns:
        HTML string with inline style attributes.
    """
    text = _escape_html(run.text)
    if not text:
        return ""

    styles: list[str] = []
    if run.bold:
        styles.append("font-weight: bold")
    if run.italic:
        styles.append("font-style: italic")
    if run.underline:
        styles.append("text-decoration: underline")
    if run.font.size:
        pt = run.font.size.pt
        styles.append(f"font-size: {pt}pt")
    if run.font.color and run.font.color.rgb:
        hex_color = str(run.font.color.rgb)
        styles.append(f"color: #{hex_color}")
    if run.font.name:
        styles.append(f"font-family: {run.font.name}")

    if styles:
        style_str = "; ".join(styles)
        return f'<span style="{style_str}">{text}</span>'
    return text


def _paragraph_to_html(p) -> str:
    """Convert a Paragraph to HTML based on its style and content.

    Handles headings (h1-h6), lists, title, subtitle, and normal paragraphs.

    Args:
        p: A python-docx Paragraph object.

    Returns:
        HTML string representation of the paragraph.
    """
    style_name = p.style.name if p.style else ""

    runs_html = "".join(_run_to_html(r) for r in p.runs)
    if not runs_html.strip():
        runs_html = "&nbsp;"

    align = ""
    if p.alignment is not None:
        align_map = {
            1: "left", 2: "center", 3: "right", 4: "justify",
        }
        align_val = align_map.get(p.alignment, "")
        if align_val:
            align = f" text-align: {align_val};"

    if style_name.startswith("Heading"):
        try:
            level = int(style_name.split()[-1])
        except (ValueError, IndexError):
            level = 1
        level = min(max(level, 1), 6)
        return f"<h{level} style=\"margin: 12px 0 6px;\">{runs_html}</h{level}>"

    if style_name == "List Bullet":
        return f"<li>{runs_html}</li>"
    if style_name == "List Number":
        return f"<li>{runs_html}</li>"

    if "Title" in style_name:
        return f'<h1 style="margin: 16px 0 8px; font-size: 24pt;">{runs_html}</h1>'
    if "Subtitle" in style_name:
        return f'<h2 style="margin: 12px 0 6px; font-size: 18pt; color: #555;">{runs_html}</h2>'

    return f'<p style="margin: 4px 0;{align}">{runs_html}</p>'


def _table_to_html(table) -> str:
    """Convert a Table to an HTML table.

    Args:
        table: A python-docx Table object.

    Returns:
        HTML table string with borders and padding.
    """
    rows_html: list[str] = []
    for row in table.rows:
        cells_html: list[str] = []
        for cell in row.cells:
            cell_content = "".join(_paragraph_to_html(p) for p in cell.paragraphs)
            if not cell_content.strip():
                cell_content = "&nbsp;"
            cells_html.append(
                f'<td style="border: 1px solid #ccc; padding: 6px;">{cell_content}</td>'
            )
        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")
    return (
        '<table style="border-collapse: collapse; width: 100%; margin: 8px 0;">'
        f"{''.join(rows_html)}</table>"
    )


def parse_docx(path: str) -> DocxResult:
    """Parse a DOCX file using python-docx, producing rich HTML.

    Preserves formatting (bold, italic, headings, lists, tables).

    Args:
        path: Path to the DOCX file.

    Returns:
        DocxResult with HTML content and paragraph count.
    """
    try:
        import docx
    except ImportError:
        return {"type": "docx", "content": "[python-docx not installed]", "paragraphs": 0, **file_meta(path)}

    doc = docx.Document(path)
    parts: list[str] = []
    para_count = 0

    from docx.table import Table as DocxTable
    from docx.text.paragraph import Paragraph

    for item in doc.iter_inner_content():
        if isinstance(item, Paragraph):
            parts.append(_paragraph_to_html(item))
            para_count += 1
        elif isinstance(item, DocxTable):
            parts.append(_table_to_html(item))

    html = (
        '<div style="padding: 20px; font-family: sans-serif; line-height: 1.6;">'
        f"{''.join(parts)}</div>"
    )

    return {
        "type": "docx",
        "content": html,
        "paragraphs": para_count,
        **file_meta(path),
    }
