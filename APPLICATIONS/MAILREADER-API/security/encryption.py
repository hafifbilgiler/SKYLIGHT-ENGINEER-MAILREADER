import json
from cryptography.fernet import Fernet
from app.config import MASTER_KEY

def _fernet() -> Fernet:
    if not MASTER_KEY:
        raise RuntimeError("MAILREADER_MASTER_KEY is not set")
    return Fernet(MASTER_KEY.encode("utf-8"))

def encrypt_payload(payload: dict) -> str:
    """
    Encrypt JSON payload. API asla plaintext döndürmez.
    """
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    token = _fernet().encrypt(data)
    return token.decode("utf-8")

def decrypt_payload(enc_payload: str) -> dict:
    """
    INTERNAL use (ileride mail fetcher). UI/API response içinde asla kullanılmayacak.
    """
    raw = _fernet().decrypt(enc_payload.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))
