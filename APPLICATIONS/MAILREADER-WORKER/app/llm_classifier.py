import os
import requests

LLM_URL = (os.getenv("LLM_BASE_URL") or "").rstrip("/")

PROMPT = """You are a mail classifier.

Categories:
- important
- normal
- spam

Return STRICT JSON only:
{"category":"important|normal|spam","confidence":0-100,"reason":"short"}

Email:
Subject: {subject}
From: {sender}
To: {to}
"""


def classify(mail: dict) -> tuple[str, int, str]:
    """
    Returns (category, confidence, reason)
    If LLM fails -> normal, 50, "llm_error"
    """
    if not LLM_URL:
        return "normal", 50, "llm_disabled"

    payload = {
        "prompt": PROMPT.format(
            subject=mail.get("subject", "") or "",
            sender=mail.get("from", "") or "",
            to=mail.get("to", "") or "",
        ),
        "temperature": 0.0,
        "n_predict": 128
    }

    try:
        r = requests.post(f"{LLM_URL}/completion", json=payload, timeout=60)
        r.raise_for_status()
        content = (r.json().get("content") or "").strip()

        # llama.cpp sometimes returns raw JSON string, sometimes with spaces/newlines
        # Try to parse robustly without extra deps.
        import json
        data = json.loads(content)

        category = (data.get("category") or "normal").strip().lower()
        confidence = int(data.get("confidence") or 50)
        reason = (data.get("reason") or "llm").strip()[:200]

        if category not in ("important", "normal", "spam"):
            category = "normal"

        if confidence < 0:
            confidence = 0
        if confidence > 100:
            confidence = 100

        return category, confidence, reason

    except Exception:
        return "normal", 50, "llm_error"
