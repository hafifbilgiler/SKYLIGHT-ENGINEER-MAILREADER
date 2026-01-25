import os
import re
import json
import requests

# =========================================================
# CONFIG
# =========================================================
LLM_URL = (os.getenv("LLM_BASE_URL") or "").rstrip("/")

# =========================================================
# HELPERS
# =========================================================
def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    return re.findall(r"https?://[^\s<>\"]+", text, re.IGNORECASE)


def extract_suspicious_signals(body: str) -> dict:
    body_lower = body.lower()

    signals = {
        "has_http": False,
        "has_shortener": False,
        "urgent_words": False,
        "credential_words": False,
        "financial_words": False,
    }

    urls = extract_urls(body)
    if any(u.startswith("http://") for u in urls):
        signals["has_http"] = True

    if any(x in body_lower for x in ["bit.ly", "tinyurl", "t.co"]):
        signals["has_shortener"] = True

    if any(x in body_lower for x in ["urgent", "immediately", "action required", "verify now"]):
        signals["urgent_words"] = True

    if any(x in body_lower for x in ["password", "login", "verify account", "security check"]):
        signals["credential_words"] = True

    if any(x in body_lower for x in ["invoice", "payment", "crypto", "wallet", "bank"]):
        signals["financial_words"] = True

    return signals


# =========================================================
# PROMPT
# =========================================================
PROMPT = """
You are an advanced email security classifier.

Your task is to classify an email into ONE category.

Categories:
- important (personal, trusted, work, real notifications)
- normal (newsletters, promotions, neutral)
- spam (phishing, scam, fraud, fake offers)

IMPORTANT RULES:
- Analyze SUBJECT and BODY together
- Look for phishing tricks:
  - fake company names
  - misleading URLs
  - HTTP links instead of HTTPS
  - urgency or fear tactics
  - credential or payment requests
- Promotions or discounts are NOT important unless explicitly requested by the user
- If suspicious → spam
- Be conservative: do NOT mark important unless clearly important

Return STRICT JSON ONLY:
{
  "category": "important|normal|spam",
  "confidence": 0-100,
  "reason": "short explanation"
}

Email:
Subject: {subject}
From: {sender}
To: {to}
Body:
{body}

Extra Signals:
{signals}
"""


# =========================================================
# MAIN CLASSIFIER
# =========================================================
def classify(mail: dict) -> tuple[str, int, str]:
    """
    Returns (category, confidence, reason)
    Safe fallback if LLM fails
    """

    if not LLM_URL:
        return "normal", 50, "llm_disabled"

    body = mail.get("body", "") or ""
    signals = extract_suspicious_signals(body)

    payload = {
        "prompt": PROMPT.format(
            subject=mail.get("subject", "") or "",
            sender=mail.get("from", "") or "",
            to=mail.get("to", "") or "",
            body=body[:4000],  # safety limit
            signals=json.dumps(signals),
        ),
        "temperature": 0.0,
        "n_predict": 256,
    }

    try:
        r = requests.post(
            f"{LLM_URL}/completion",
            json=payload,
            timeout=90,
        )
        r.raise_for_status()

        content = (r.json().get("content") or "").strip()

        # LLM MUST return JSON
        data = json.loads(content)

        category = (data.get("category") or "normal").lower().strip()
        confidence = int(data.get("confidence") or 50)
        reason = (data.get("reason") or "llm").strip()[:200]

        if category not in ("important", "normal", "spam"):
            category = "normal"

        confidence = max(0, min(confidence, 100))

        return category, confidence, reason

    except Exception as e:
        return "normal", 50, "llm_error"


# =========================================================
# OPTIONAL ENRICHMENT (future use)
# =========================================================
def enrich_mail(mail: dict) -> dict:
    body = mail.get("body", "") or ""
    urls = extract_urls(body)

    mail["urls"] = urls
    mail["has_http"] = any(u.startswith("http://") for u in urls)

    return mail
