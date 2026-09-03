from typing import TypedDict
from ._meta import FileMeta, file_meta


class PdfResult(FileMeta):
    type: str
    content: str
    pages: int
    page_texts: list[dict]


class DocxResult(FileMeta):
    type: str
    content: str
    paragraphs: int


def parse_pdf(path: str) -> PdfResult:
    """Parse a PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        return {"type": "pdf", "content": "[pdfplumber not installed]", "pages": 0, "page_texts": [], **file_meta(path)}

    pages: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page": i + 1, "text": text})

    full_text = "\n\n".join(p["text"] for p in pages)
    return {
        "type": "pdf",
        "content": full_text,
        "pages": len(pages),
        "page_texts": pages,
        **file_meta(path),
    }


def parse_docx(path: str) -> DocxResult:
    """Parse a DOCX file using python-docx."""
    try:
        import docx
    except ImportError:
        return {"type": "docx", "content": "[python-docx not installed]", "paragraphs": 0, **file_meta(path)}

    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return {
        "type": "docx",
        "content": "\n".join(paragraphs),
        "paragraphs": len(paragraphs),
        **file_meta(path),
    }
