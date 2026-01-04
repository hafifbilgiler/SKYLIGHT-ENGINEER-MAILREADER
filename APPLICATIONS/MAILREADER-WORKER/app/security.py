import os
import json
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = os.getenv("MAILREADER_MASTER_KEY", "").strip()
    if not key:
        raise RuntimeError("MAILREADER_MASTER_KEY is not set")
    return Fernet(key.encode())


def decrypt_payload(enc_payload: str) -> dict:
    f = _get_fernet()
    raw = f.decrypt(enc_payload.encode()).decode("utf-8")
    return json.loads(raw)


def encrypt_payload(payload: dict) -> str:
    f = _get_fernet()
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return f.encrypt(raw).decode("utf-8")
