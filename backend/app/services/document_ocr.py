"""Document text extraction with an explicit OCR capability probe.

Two backends are supported for images and scanned PDFs:

* **PyMuPDF** — rasterises pages, then OCRs them with Tesseract when available.
* **pytesseract** — direct wrapper used for image uploads.

If no OCR engine is installed the module reports ``ocr_available == False`` and
callers must surface that to the user instead of pretending extraction succeeded.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Capability probe (runs once, cached) ──────────────────────────────
_OCR_STATE: dict[str, object] | None = None


def _probe() -> dict[str, object]:
    global _OCR_STATE
    if _OCR_STATE is not None:
        return _OCR_STATE

    state: dict[str, object] = {
        "pymupdf": False,
        "pytesseract": False,
        "tesseract_binary": False,
        "pillow": False,
        "reason": None,
    }
    try:
        import fitz  # noqa: F401  (PyMuPDF)

        state["pymupdf"] = True
    except Exception:
        state["reason"] = "PyMuPDF is not installed; PDF text extraction is unavailable."
    try:
        import PIL  # noqa: F401

        state["pillow"] = True
    except Exception:
        pass
    try:
        import pytesseract

        state["pytesseract"] = True
        try:
            pytesseract.get_tesseract_version()
            state["tesseract_binary"] = True
        except Exception:
            if state["reason"] is None:
                state["reason"] = (
                    "The Tesseract OCR engine is not installed on the server, so "
                    "scanned documents and images cannot be read."
                )
    except Exception:
        if state["reason"] is None:
            state["reason"] = "pytesseract is not installed; OCR is unavailable."

    _OCR_STATE = state
    return state


def ocr_available() -> bool:
    state = _probe()
    return bool(state["pytesseract"] and state["tesseract_binary"])


def ocr_status() -> dict:
    state = _probe()
    available = ocr_available()
    return {
        "available": available,
        "engine": "tesseract" if available else None,
        "pdf_text": bool(state["pymupdf"]),
        "detail": None
        if available
        else state["reason"]
        or "OCR is not available in this environment.",
    }


# ── Extraction ────────────────────────────────────────────────────────
class ExtractionError(Exception):
    """Raised when a document cannot be read at all."""


@dataclass
class Extraction:
    text: str
    method: str  # "pdf-text" | "ocr" | "plain-text"
    pages: int = 1
    ocr_used: bool = False


def _pdf_text(data: bytes) -> Extraction:
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ExtractionError("This file is not a readable PDF.") from exc

    try:
        if doc.needs_pass:
            raise ExtractionError("This PDF is password protected and cannot be read.")
        chunks: list[str] = []
        pages = doc.page_count
        for page in doc:
            chunks.append(page.get_text("text") or "")
        text = "\f".join(chunks).strip()
        if len(text) > 40:
            return Extraction(text=text, method="pdf-text", pages=pages)

        # No embedded text → likely a scanned document; try OCR on rendering.
        if not ocr_available():
            raise ExtractionError(
                "This PDF has no embedded text layer (it looks scanned), and OCR is not "
                "available on this server. Upload a text-based PDF or ask the "
                "administrator to enable OCR."
            )
        return _ocr_pdf(doc, pages)
    finally:
        doc.close()


def _ocr_pdf(doc, pages: int) -> Extraction:
    import fitz
    import pytesseract
    from PIL import Image

    chunks: list[str] = []
    for index, page in enumerate(doc):
        if index >= 10:  # bounded work
            break
        pixmap = page.get_pixmap(dpi=220)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        chunks.append(pytesseract.image_to_string(image))
    text = "\f".join(chunks).strip()
    if not text:
        raise ExtractionError(
            "OCR ran but no text could be recognised in this PDF."
        )
    return Extraction(text=text, method="ocr", pages=pages, ocr_used=True)


def _image_text(data: bytes) -> Extraction:
    if not ocr_available():
        raise ExtractionError(
            "Image uploads need OCR, which is not available on this server. "
            "Upload a text-based PDF instead, or ask the administrator to enable OCR."
        )
    import pytesseract
    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError) as exc:
        raise ExtractionError("This image could not be opened.") from exc

    text = pytesseract.image_to_string(image).strip()
    if not text:
        raise ExtractionError(
            "OCR ran but found no readable text in this image. Try a higher-resolution "
            "scan or a text-based PDF."
        )
    return Extraction(text=text, method="ocr", ocr_used=True)


def extract_document(data: bytes, filename: str, content_type: str = "") -> Extraction:
    """Extract text from a PDF, image or plain-text report."""
    if not data:
        raise ExtractionError("The uploaded file is empty.")

    if data.startswith(b"%PDF"):
        return _pdf_text(data)

    lowered = (filename or "").lower()
    is_image = (
        content_type.startswith("image/")
        or lowered.endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"))
    )
    if is_image:
        return _image_text(data)

    # Plain text fallback for .txt/.csv exports.
    if lowered.endswith((".txt", ".csv")) or content_type.startswith("text/"):
        try:
            text = data.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise ExtractionError("This text file is not UTF-8 encoded.") from exc
        if len(text) < 5:
            raise ExtractionError("This file contains no readable text.")
        return Extraction(text=text, method="plain-text")

    raise ExtractionError(
        "Unsupported file type. Upload a PDF, a PNG/JPEG image, or a plain-text export."
    )
