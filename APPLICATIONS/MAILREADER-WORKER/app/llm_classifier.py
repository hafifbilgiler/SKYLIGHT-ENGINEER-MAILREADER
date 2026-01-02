import os, requests

LLM_URL = os.getenv("LLM_BASE_URL")

PROMPT = """Classify this email as one of:
important, normal, spam

Return ONLY the label.

Subject: {subject}
From: {sender}
"""

def classify(mail):
    payload = {
        "prompt": PROMPT.format(
            subject=mail.get("subject", ""),
            sender=mail.get("from", "")
        ),
        "temperature": 0.0,
        "n_predict": 8
    }
    r = requests.post(f"{LLM_URL}/completion", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["content"].strip().lower()
