"""CV upload handling: text extraction, OCR preparation and a short-lived profile store.

Only the structured profile is kept (never the raw CV), in memory, for a
limited time — nothing is written to disk.
"""

import io
import re
import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from .schemas import CandidateProfile

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 15_000
MIN_TEXT_CHARS = 200
TEXT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS

# Images sent to the vision model: long side capped, JPEG-encoded to stay well under API limits.
OCR_MAX_SIDE = 2000
OCR_PDF_SCALE = 2.5  # ~180 DPI for A4
OCR_JPEG_QUALITY = 85


class CVError(ValueError):
    """Raised when an uploaded file cannot be used as a CV."""


@dataclass
class CVDocument:
    """Either extracted text, or page images that still need OCR."""

    text: str = ""
    images: list[bytes] = field(default_factory=list)

    @property
    def needs_ocr(self) -> bool:
        return not self.text and bool(self.images)


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise CVError("Şifrəli PDF oxuna bilmir.")
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _docx_text(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def _to_jpeg(image) -> bytes:
    image = image.convert("RGB")
    image.thumbnail((OCR_MAX_SIDE, OCR_MAX_SIDE))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=OCR_JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


def _render_pdf_pages(data: bytes, max_pages: int) -> list[bytes]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        pages = []
        for index in range(min(len(pdf), max_pages)):
            page = pdf[index]
            pages.append(_to_jpeg(page.render(scale=OCR_PDF_SCALE).to_pil()))
            page.close()
        return pages
    finally:
        pdf.close()


def _prepare_image(data: bytes) -> bytes:
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return _to_jpeg(ImageOps.exif_transpose(image))


def normalize_text(text: str) -> str:
    """Collapse whitespace, require a minimum amount of text and cap the length."""
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) < MIN_TEXT_CHARS:
        raise CVError("CV-dən kifayət qədər mətn çıxarıla bilmədi.")
    return text[:MAX_TEXT_CHARS]


def load_cv(filename: str, data: bytes, max_ocr_pages: int = 4) -> CVDocument:
    """Read a CV upload. Scanned PDFs and photos come back as images for OCR. Blocking."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise CVError("Yalnız PDF, DOCX, TXT, MD və ya şəkil (JPG, PNG, WEBP) yükləyin.")

    try:
        if suffix in IMAGE_EXTENSIONS:
            return CVDocument(images=[_prepare_image(data)])
        if suffix == ".pdf":
            text = _pdf_text(data)
            try:
                return CVDocument(text=normalize_text(text))
            except CVError:
                # No text layer (scanned or image-only PDF) — fall back to OCR.
                return CVDocument(images=_render_pdf_pages(data, max_ocr_pages))
        if suffix == ".docx":
            return CVDocument(text=normalize_text(_docx_text(data)))
        return CVDocument(text=normalize_text(data.decode("utf-8", errors="replace")))
    except CVError:
        raise
    except Exception as exc:
        raise CVError("Fayl oxuna bilmədi — zədələnmiş ola bilər.") from exc


class ProfileStore:
    """Tiny TTL + size-bounded store keyed by an unguessable id."""

    def __init__(self, ttl_seconds: int = 2 * 60 * 60, max_items: int = 200):
        self._ttl = ttl_seconds
        self._max = max_items
        self._items: OrderedDict[str, tuple[float, CandidateProfile]] = OrderedDict()

    def put(self, profile: CandidateProfile) -> str:
        self._evict()
        cv_id = secrets.token_urlsafe(16)
        self._items[cv_id] = (time.monotonic() + self._ttl, profile)
        while len(self._items) > self._max:
            self._items.popitem(last=False)
        return cv_id

    def get(self, cv_id: str) -> CandidateProfile | None:
        self._evict()
        item = self._items.get(cv_id)
        return item[1] if item else None

    def _evict(self) -> None:
        now = time.monotonic()
        for key in [k for k, (expires, _) in self._items.items() if expires < now]:
            del self._items[key]
