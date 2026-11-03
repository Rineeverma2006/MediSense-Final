"""Report analysis: abnormality detection and cross-report comparison.

Reference ranges come **only** from the uploaded report. Missing ranges are reported
as ``no_reference_range`` — nothing is invented.
"""
from __future__ import annotations

from .report_extraction import Parameter

DISCLAIMER = (
    "Informational only. Not a diagnosis or medical advice. "
    "Reference ranges are those printed in the uploaded report; "
    "discuss results with a qualified clinician."
)

# Display group used by the UI to organise findings.
GROUP_HINTS = (
    ("lipid", ("cholesterol", "ldl", "hdl", "triglycerid", "vldl")),
    ("liver", ("sgpt", "sgot", "alt", "ast", "bilirubin", "alkaline", "albumin", "globulin")),
    ("blood", ("haemoglobin", "hemoglobin", "rbc", "wbc", "platelet", "haematocrit",
               "hematocrit", "mcv", "mch", "mchc", "neutrophil", "lymphocyte",
               "monocyte", "eosinophil", "basophil", "esr")),
    ("diabetes", ("glucose", "hba1c", "insulin", "fructosamine")),
    ("kidney", ("creatinine", "urea", "bun", "egfr", "uric")),
    ("thyroid", ("tsh", "t3", "t4", "thyroid")),
    ("vitamins", ("vitamin", "ferritin", "iron", "calcium", "magnesium", "folate", "b12")),
)


def classify(p: Parameter) -> str:
    if p.ref_low is None or p.ref_high is None:
        return "no_reference_range"
    if p.value < p.ref_low:
        return "below_range"
    if p.value > p.ref_high:
        return "above_range"
    return "within_range"


def group_for(name: str) -> str:
    lowered = name.lower()
    for group, needles in GROUP_HINTS:
        if any(needle in lowered for needle in needles):
            return group
    return "other"


def _severity(p: Parameter, status: str) -> str:
    """Relative deviation from the printed range — a signal, not a diagnosis."""
    if status == "no_reference_range" or p.ref_low is None or p.ref_high is None:
        return "unknown"
    if status == "within_range":
        return "normal"
    span = p.ref_high - p.ref_low
    if span <= 0:
        return "moderate"
    deviation = (p.ref_low - p.value) / span if status == "below_range" else (p.value - p.ref_high) / span
    if deviation >= 0.5:
        return "high"
    if deviation >= 0.2:
        return "moderate"
    return "mild"


def analyze(params: list[Parameter]) -> dict:
    rows = []
    for p in params:
        status = classify(p)
        rows.append(
            {
                **p.as_dict(),
                "status": status,
                "severity": _severity(p, status),
                "group": group_for(p.name),
            }
        )
    flagged = [r for r in rows if r["status"] in ("below_range", "above_range")]
    no_range = [r for r in rows if r["status"] == "no_reference_range"]
    within = [r for r in rows if r["status"] == "within_range"]
    groups = sorted({r["group"] for r in rows})

    summary_parts = [
        f"{len(rows)} parameter{'s' if len(rows) != 1 else ''} extracted",
        f"{len(flagged)} outside the printed reference range",
    ]
    if no_range:
        summary_parts.append(f"{len(no_range)} without a printed range")

    return {
        "parameters": rows,
        "summary": "; ".join(summary_parts) + ".",
        "flagged": [r["name"] for r in flagged],
        "counts": {
            "total": len(rows),
            "flagged": len(flagged),
            "within_range": len(within),
            "no_reference_range": len(no_range),
        },
        "groups": groups,
        "disclaimer": DISCLAIMER,
    }


def compare(old: dict, new: dict) -> list[dict]:
    """Backward-compatible comparison: a flat row list (name/previous/current/change/unit)."""
    return [
        {
            "name": row["name"],
            "previous": row["previous"],
            "current": row["current"],
            "change": row["change"],
            "unit": row["unit"],
        }
        for row in compare_detailed(old, new)["rows"]
        if row["previous"] is not None
    ]


def compare_detailed(old: dict, new: dict) -> dict:
    """Compare two analysed reports parameter-by-parameter."""
    prev = {r["name"].lower(): r for r in old.get("parameters", [])}
    rows = []
    for r in new.get("parameters", []):
        o = prev.get(r["name"].lower())
        if not o:
            rows.append(
                {
                    "name": r["name"],
                    "previous": None,
                    "current": r["value"],
                    "change": None,
                    "percent_change": None,
                    "unit": r.get("unit", ""),
                    "direction": "new",
                    "status": r.get("status"),
                }
            )
            continue
        change = round(r["value"] - o["value"], 4)
        pct = round((change / o["value"]) * 100, 2) if o["value"] else None
        direction = "stable" if abs(change) < 1e-9 else ("up" if change > 0 else "down")
        rows.append(
            {
                "name": r["name"],
                "previous": o["value"],
                "current": r["value"],
                "change": change,
                "percent_change": pct,
                "unit": r.get("unit", ""),
                "direction": direction,
                "status": r.get("status"),
                "previous_status": o.get("status"),
            }
        )

    improved = [
        x for x in rows
        if x.get("previous_status") in ("above_range", "below_range")
        and x.get("status") == "within_range"
    ]
    worsened = [
        x for x in rows
        if x.get("previous_status") == "within_range"
        and x.get("status") in ("above_range", "below_range")
    ]
    return {
        "rows": rows,
        "compared": len([x for x in rows if x["previous"] is not None]),
        "new_parameters": len([x for x in rows if x["direction"] == "new"]),
        "improved": [x["name"] for x in improved],
        "worsened": [x["name"] for x in worsened],
        "summary": (
            f"{len(rows)} parameters compared; {len(improved)} moved into range, "
            f"{len(worsened)} moved out of range."
        ),
        "disclaimer": DISCLAIMER,
    }
