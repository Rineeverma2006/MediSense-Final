"""Medical report upload, analysis, listing and comparison."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api import schemas
from app.api.deps import current_user, db, log_action, notify, require
from app.core.config import MAX_UPLOAD_BYTES
from app.database.models import Report, User
from app.services import report_analysis as analysis
from app.services import report_extraction as extraction
from app.services.document_ocr import ExtractionError, extract_document, ocr_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])

MAX_MB = MAX_UPLOAD_BYTES // (1024 * 1024)


def _owned(s: Session, report_id: int, user: User) -> Report:
    report = s.query(Report).filter_by(id=report_id, user_id=user.id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


def _detail(report: Report) -> dict:
    payload = {"id": report.id, "filename": report.filename,
               "created_at": report.created_at.isoformat()}
    payload.update(json.loads(report.analysis_json))
    return payload


@router.get("/ocr-status")
def ocr_capabilities():
    """Tell the UI whether scanned documents/images can be read here."""
    return ocr_status()


@router.post("/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    user: User = Depends(require("patient", "doctor")),
    s: Session = Depends(db),
):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(422, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Maximum upload size is {MAX_MB} MB")

    try:
        document = extract_document(data, file.filename or "", file.content_type or "")
    except ExtractionError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        logger.exception("Unexpected extraction failure")
        raise HTTPException(422, "Could not read this document.")

    params = extraction.dedupe(extraction.extract_parameters(document.text))
    if not params:
        preview = " ".join(document.text.split())[:900]
        preview_hint = (
            f" Extracted text preview: {preview}"
            if preview
            else " No readable text was extracted; this may be a low-quality scan or an image-only PDF."
        )
        raise HTTPException(
            422,
            "No supported lab parameters were detected. Check the extracted text and "
            "try a clearer PDF or image with parameter names and numeric results."
            + preview_hint,
        )

    result = analysis.analyze(params)
    result["extraction"] = {
        "method": document.method,
        "pages": document.pages,
        "ocr_used": document.ocr_used,
    }
    result["filename"] = (file.filename or "medical-report")[:255]

    report = Report(
        user_id=user.id,
        filename=result["filename"],
        analysis_json=json.dumps(result),
    )
    s.add(report)
    s.commit()
    s.refresh(report)
    log_action(s, user.id, f"report_analyzed:{report.id}", commit=False)
    if result["counts"]["flagged"]:
        notify(
            s,
            user.id,
            "Report analysed",
            f"{result['counts']['flagged']} value(s) fall outside the printed reference range.",
            type="warning",
        )
    else:
        s.commit()

    return {"id": report.id, "filename": report.filename,
            "created_at": report.created_at.isoformat(), **result}


@router.get("")
def list_reports(user: User = Depends(current_user), s: Session = Depends(db)):
    rows = (
        s.query(Report)
        .filter_by(user_id=user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    out = []
    for report in rows:
        try:
            counts = json.loads(report.analysis_json).get("counts", {})
        except (ValueError, TypeError):
            counts = {}
        out.append(
            {
                "id": report.id,
                "filename": report.filename,
                "created_at": report.created_at.isoformat(),
                "flagged": counts.get("flagged", 0),
                "total_parameters": counts.get("total", 0),
            }
        )
    return out


@router.get("/{report_id}")
def report_detail(
    report_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    report = _owned(s, report_id, user)
    log_action(s, user.id, f"report_viewed:{report_id}")
    return _detail(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    report = _owned(s, report_id, user)
    s.delete(report)
    s.commit()
    log_action(s, user.id, f"report_deleted:{report_id}")
    return {"status": "deleted", "id": report_id}


@router.post("/compare")
def compare_reports(
    body: schemas.ReportCompareIn,
    user: User = Depends(current_user),
    s: Session = Depends(db),
):
    ids = body.report_ids
    older_id, newer_id = ids[0], ids[1]
    older, newer = _owned(s, older_id, user), _owned(s, newer_id, user)

    # Compare chronologically regardless of the order the user picked them.
    if older.created_at and newer.created_at and older.created_at > newer.created_at:
        older, newer = newer, older

    result = analysis.compare_detailed(
        json.loads(older.analysis_json), json.loads(newer.analysis_json)
    )
    return {
        "older": {"id": older.id, "filename": older.filename,
                  "created_at": older.created_at.isoformat()},
        "newer": {"id": newer.id, "filename": newer.filename,
                  "created_at": newer.created_at.isoformat()},
        **result,
    }
