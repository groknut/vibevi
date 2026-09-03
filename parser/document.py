import os
import tempfile
from typing import TypedDict
from ._meta import FileMeta, file_meta


class PdfPageImage(TypedDict):
    page: int
    image_path: str


class PdfResult(FileMeta):
    type: str
    content: str
    pages: int
    page_images: list[PdfPageImage]


class DocxResult(FileMeta):
    type: str
    content: str
    paragraphs: int


def parse_pdf(path: str) -> PdfResult:
    """Parse a PDF file using PyMuPDF, rendering pages as images."""
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
