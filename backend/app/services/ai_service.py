"""AI assistant service.

Provider resolution order:
  1. ``AI_PROVIDER`` env var (demo | gemini | openai)
  2. the first provider that has an API key
  3. labelled demo mode

Live providers are called **server-side only** — API keys never reach the browser.
Demo answers are deterministic educational text and are always labelled ``mode=demo``
so the UI never presents them as a live model response.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

import httpx

from app.core.config import (
    AI_TIMEOUT_SECONDS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    provider_status,
)

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "MediSense provides general educational information only. "
    "It does not diagnose, prescribe, or replace a qualified clinician. "
    "For urgent symptoms contact your local emergency service."
)

SYSTEM_PROMPT = (
    "You are MediSense, a careful healthcare information assistant inside a patient "
    "health platform. Rules you must follow:\n"
    "1. Explain medical terms and reports in clear, calm language.\n"
    "2. Never diagnose, never prescribe, never suggest starting/stopping/changing a "
    "medication or dose.\n"
    "3. Always recommend discussing findings with a qualified clinician.\n"
    "4. If symptoms sound like an emergency (chest pain, stroke signs, severe bleeding, "
    "difficulty breathing, suicidal thoughts) tell the user to seek emergency care now.\n"
    "5. Never invent lab reference ranges; ranges must come from the user's own report.\n"
    "6. Do not request or repeat sensitive identifiers such as government IDs.\n"
    "Keep answers under 200 words and use short paragraphs or bullet points."
)

# Deterministic demo answers, one per topic returned by the classifier.
DEMO_ANSWERS = {
    "emergency": (
        "The symptoms you described could need urgent assessment. Please contact your local "
        "emergency service now or go to the nearest emergency department. Do not wait for a "
        "chat response to decide what to do."
    ),
    "blood": (
        "A complete blood count (CBC) measures red cells, white cells, platelets and "
        "haemoglobin. Haemoglobin carries oxygen; low values can appear with anaemia, "
        "blood loss or nutritional deficiencies, while high values have other causes. "
        "One number is never enough for a conclusion — the laboratory range printed on "
        "your report and your symptoms both matter."
    ),
    "lipid": (
        "A lipid profile usually reports total cholesterol, LDL, HDL and triglycerides. "
        "LDL carries cholesterol to tissues and HDL helps clear it; triglycerides relate "
        "to energy storage. Compare each result only with the reference range printed by "
        "your laboratory, because targets differ with personal cardiovascular risk."
    ),
    "liver": (
        "Liver panels commonly include ALT/SGPT, AST/SGOT, alkaline phosphatase and "
        "bilirubin. These enzymes can rise for many reasons including fatty liver, "
        "infection, medicines or alcohol. A single abnormal value does not establish a "
        "diagnosis; trends over time and your clinical context matter."
    ),
    "diabetes": (
        "Fasting glucose, post-meal glucose and HbA1c measure blood sugar differently. "
        "HbA1c reflects roughly the last two to three months. Interpretation depends on "
        "the test type, timing and the laboratory's own range, so ask your clinician "
        "which target applies to you."
    ),
    "doctor": (
        "Useful questions for your appointment: What does this result mean for me "
        "specifically? Should it be repeated, and when? Do any of my medicines or "
        "conditions affect it? What symptoms should make me seek urgent care? What "
        "change would you expect to see next time?"
    ),
    "pressure": (
        "Blood pressure has two numbers: systolic pressure (when the heart contracts) and "
        "diastolic pressure (between beats). Readings can vary with activity, stress, posture, "
        "and cuff fit. Use the range and instructions from your clinician; repeated readings "
        "and your medical history matter more than one measurement."
    ),
    "sleep": (
        "Sleep quality is affected by routine, light, stress, caffeine, medicines, and health "
        "conditions. A regular sleep and wake time, a dark quiet room, and limiting late-day "
        "caffeine may help. Persistent insomnia, loud snoring, or severe daytime sleepiness "
        "is worth discussing with a clinician."
    ),
    "medication": (
        "I can explain general medication terms, but I cannot tell you to start, stop, or "
        "change a medicine or dose. Check the label and contact your prescriber or pharmacist "
        "about your specific medicine, interactions, or side effects."
    ),
    "report": (
        "I can help explain the values from a report you share, but I cannot see your reports "
        "in this conversation yet. You can upload one in Report Analyzer or paste a test name, "
        "result, units, and the lab's reference range. Please leave out personal identifiers."
    ),
    "general": (
        "I can explain common medical terms, summarise a report you upload, and help you "
        "prepare questions for a clinician. I cannot diagnose conditions or recommend "
        "starting, stopping or changing medication. Tell me which term or result you "
        "would like explained."
    ),
}


def _demo_topic(message: str) -> str:
    """Match health terms on word boundaries, including common Hindi/Hinglish terms."""
    text = re.sub(r"\s+", " ", message.casefold()).strip()
    checks = (
        ("emergency", ("chest pain", "seene me dard", "seene mein dard", "can't breathe", "cannot breathe", "difficulty breathing", "trouble breathing", "saans nahi", "saans lene mein", "severe bleeding", "stroke", "face drooping", "suicid", "self harm", "overdose")),
        ("lipid", ("cholesterol", "cholestrol", "ldl", "hdl", "triglyceride", "lipid", "charbi")),
        ("pressure", ("blood pressure", "bp reading", "bp", "hypertension", "systolic", "diastolic", "blood pressure", "blood pressure")),
        ("diabetes", ("blood sugar", "sugar level", "glucose", "diabetes", "hba1c", "a1c", "blood sugar", "sugar")),
        ("liver", ("liver", "jigar", "sgpt", "sgot", "bilirubin", "alt", "ast")),
        ("blood", ("cbc", "hemoglobin", "haemoglobin", "anemia", "anaemia", "platelet", "white blood cell", "khoon", "khoon ki")),
        ("sleep", ("sleep", "insomnia", "snoring", "neend", "nind")),
        ("medication", ("medicine", "medication", "dawa", "dawai", "drug interaction", "side effect", "dose")),
        ("doctor", ("doctor", "clinician", "appointment", "what should i ask", "doctor se kya")),
        ("report", ("my report", "latest report", "lab report", "test result", "my results", "report samjhao", "report explain")),
    )
    for label, terms in checks:
        for term in terms:
            pattern = r"(?<!\w)" + r"\s+".join(re.escape(part) for part in term.split()) + r"(?!\w)"
            if re.search(pattern, text):
                return label
    return "general"


def _demo_reply(message: str, notice: str | None = None) -> dict:
    label = _demo_topic(message)
    payload = {
        "mode": "demo",
        "live": False,
        "topic": label,
        "answer": DEMO_ANSWERS.get(label, DEMO_ANSWERS["general"]),
        "disclaimer": DISCLAIMER,
    }
    if notice:
        payload["notice"] = notice
    return payload


def _history_messages(history: Iterable[dict] | None) -> list[dict]:
    messages = []
    for item in history or []:
        role = "assistant" if item.get("role") == "assistant" else "user"
        content = str(item.get("content", ""))[:4000]
        if content:
            messages.append({"role": role, "content": content})
    return messages


def _call_gemini(message: str, history: list[dict]) -> str:
    contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in history
    ]
    contents.append({"role": "user", "parts": [{"text": message}]})
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 700},
    }
    with httpx.Client(timeout=AI_TIMEOUT_SECONDS) as client:
        response = client.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=body,
            headers={"Content-Type": "application/json"},
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini returned HTTP {response.status_code}")
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty answer")
    return text


def _call_openai(message: str, history: list[dict]) -> str:
    body = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *history,
                     {"role": "user", "content": message}],
        "temperature": 0.4,
        "max_tokens": 700,
    }
    with httpx.Client(timeout=AI_TIMEOUT_SECONDS) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
        )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI returned HTTP {response.status_code}")
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("OpenAI returned no choices")
    text = (choices[0].get("message") or {}).get("content", "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty answer")
    return text


def reply(message: str, history: list[dict] | None = None) -> dict:
    """Generate an assistant answer.

    Returns a dict with ``mode`` (demo|gemini|openai), ``live`` and either
    ``answer`` or ``error``. Provider failures degrade to a labelled demo answer
    that explicitly says the live provider was unreachable — the answer is never
    presented as a live model output when it is not one.
    """
    status = provider_status()
    active = status["active"]

    if active == "demo" or not status["live"]:
        return _demo_reply(message, status.get("detail"))

    trimmed = _history_messages(history)
    try:
        if active == "gemini":
            text = _call_gemini(message, trimmed)
        else:
            text = _call_openai(message, trimmed)
    except Exception as exc:  # network, quota, auth, malformed payload
        logger.warning("AI provider %s failed: %s", active, exc.__class__.__name__)
        fallback = _demo_reply(message)
        fallback["notice"] = (
            f"The configured live provider ({active}) could not be reached right now. "
            "This reply is the built-in demo answer, not a live model response."
        )
        fallback["provider_error"] = str(exc)[:200]
        return fallback

    payload = {
        "mode": active,
        "live": True,
        "model": status.get("model"),
        "answer": text,
        "disclaimer": DISCLAIMER,
    }
    # Never let live prose silently drop the safety net.
    if "clinician" not in text.lower() and "doctor" not in text.lower():
        payload["answer"] = f"{text}\n\n{DISCLAIMER}"
    return payload


def availability() -> dict:
    """Public, secret-free provider status for the UI badge."""
    status = provider_status()
    return {
        "mode": status["active"],
        "live": status["live"],
        "requested": status["requested"],
        "providers": status["configured"],
        "model": status["model"],
        "detail": status["detail"],
    }
