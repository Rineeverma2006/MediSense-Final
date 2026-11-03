"""Extract lab parameters from report text.

Only values **printed in the report** are extracted — no range is ever invented.
Supports text-based PDFs, plain text and (when an OCR backend is available) images
and scanned PDFs.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Optional

LINE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /%().\-]{1,40}?)\s*[:\-]?\s+"
    r"(?P<value>[<>]?\s*\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z%/µ^0-9.]*)\s*"
    r"(?:\(?\s*(?P<low>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(?P<high>\d+(?:\.\d+)?)\s*\)?)?\s*$"
)

# Many laboratories print result and reference limits as separate columns, which
# PDF text extraction flattens into `Test 12.4 g/dL 11.5 15.5` or
# `Test 12.4 11.5-15.5 g/dL`. Keep these patterns conservative: only accept a
# numeric result plus an explicit pair of numeric limits from the same line.
TABLE_LINE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /%().\-]{1,40}?)\s+"
    r"(?P<value>[<>]?\s*\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z%/µ^0-9.]*)\s+"
    r"(?P<low>\d+(?:\.\d+)?)\s+(?P<high>\d+(?:\.\d+)?)\s*$"
)
TABLE_DASH_LINE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /%().\-]{1,40}?)\s+"
    r"(?P<value>[<>]?\s*\d+(?:\.\d+)?)\s+"
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
    r"(?P<high>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z%/µ^0-9.]*)\s*$"
)

# "REFERENCE RANGE  13.0 - 17.0" on its own line is common in tabular reports.
RANGE_ONLY = re.compile(
    r"^\s*(?:reference\s*(?:range|interval|values?)|normal\s*range|bio\.?\s*ref\.?)\s*[:\-]?\s*"
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Header noise that should never become a parameter.
SKIP_WORDS = {
    "page", "date", "patient", "name", "age", "sex", "gender", "lab", "report",
    "sample", "collected", "received", "reported", "doctor", "referral", "address",
    "phone", "total", "method", "specimen", "barcode", "id", "no",
}


@dataclass
class Parameter:
    name: str
    value: float
    unit: str
    ref_low: Optional[float]
    ref_high: Optional[float]
    source: str = "report"
    source_page: Optional[int] = None
    confidence: float = 0.75

    def as_dict(self) -> dict:
        return asdict(self)


def _to_float(raw: str | None) -> Optional[float]:
    if not raw:
        return None
    try:
        return float(raw.replace("<", "").replace(">", "").strip())
    except ValueError:
        return None


def extract_parameters(text: str) -> list[Parameter]:
    out: list[Parameter] = []
    pending_range: tuple[float, float] | None = None

    # PDF pages are separated with form-feed by document_ocr. Plain text and
    # OCR may not have page boundaries, in which case provenance is unknown.
    for page_number, page_text in enumerate((text or "").split("\f"), start=1):
      for raw_line in page_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        range_match = RANGE_ONLY.match(line)
        if range_match:
            pending_range = (_to_float(range_match["low"]), _to_float(range_match["high"]))  # type: ignore[assignment]
            continue

        m = TABLE_LINE.match(line) or TABLE_DASH_LINE.match(line) or LINE.match(line)
        if not m:
            continue

        name = re.sub(r"\s+", " ", m["name"]).strip(" .:-")
        lowered = name.lower()
        if not name or lowered in SKIP_WORDS or len(name) < 2:
            continue
        # Reject lines whose "name" is actually a whole sentence of prose.
        if name.count(" ") > 5:
            continue

        value = _to_float(m["value"])
        if value is None:
            continue

        low, high = _to_float(m["low"]), _to_float(m["high"])
        if low is None and high is None and pending_range:
            low, high = pending_range
        pending_range = None

        out.append(
            Parameter(
                name=name,
                value=value,
                unit=(m["unit"] or "").strip(),
                ref_low=low,
                ref_high=high,
                source_page=page_number if "\f" in (text or "") else None,
                confidence=0.92 if (TABLE_LINE.match(line) or TABLE_DASH_LINE.match(line)) else 0.82,
            )
        )
    return out


def extract_text_from_pdf(data: bytes) -> str:
    """Backward-compatible helper: text from a PDF byte string.

    Delegates to :mod:`app.services.document_ocr` so OCR capability handling and
    error messages stay in one place.
    """
    from .document_ocr import extract_document

    return extract_document(data, "upload.pdf", "application/pdf").text


def dedupe(params: list[Parameter]) -> list[Parameter]:
    """Keep the first occurrence of each parameter name (case-insensitive)."""
    seen: set[str] = set()
    unique: list[Parameter] = []
    for p in params:
        key = p.name.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique
