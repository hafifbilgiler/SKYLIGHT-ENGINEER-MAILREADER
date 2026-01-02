
import os
import requests

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://skylight-engineer-mailreader-llm:8080")

def completion(prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
    url = f"{LLM_BASE_URL}/completion"
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "n_predict": max_tokens,
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return (data.get("content") or "").strip()