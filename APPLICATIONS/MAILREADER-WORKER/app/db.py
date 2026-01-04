import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

def get_accounts():
    """
    Returns list of dicts:
      {id, email, auth_method, enc_payload}
    """
    with engine.connect() as c:
        rows = c.execute(text("""
            SELECT a.id, a.email, a.auth_method, s.enc_payload
            FROM accounts a
            JOIN secrets s ON s.account_id = a.id
            ORDER BY a.created_at DESC
        """)).mappings().all()
        return [dict(r) for r in rows]


def get_rules(account_id):
    """
    Returns list of dicts:
      {name, priority, conditions, action, enabled}
    """
    with engine.connect() as c:
        rows = c.execute(text("""
            SELECT name, priority, conditions, action, enabled
            FROM rules
            WHERE account_id = :aid AND enabled = true
            ORDER BY priority DESC
        """), {"aid": account_id}).mappings().all()
        return [dict(r) for r in rows]


def update_secret_payload(account_id, enc_payload: str):
    with engine.begin() as c:
        c.execute(text("""
            UPDATE secrets
            SET enc_payload = :p
            WHERE account_id = :aid
        """), {"aid": account_id, "p": enc_payload})


def insert_email(mail: dict) -> bool:
    """
    Duplicate-safe insert (account_id + message_id).
    Returns True if inserted, False if skipped.
    """
    with engine.begin() as c:
        # Skip if message_id empty (still allow insert? => we skip to avoid spam duplicates)
        if not mail.get("message_id"):
            return False

        # Atomic-ish "insert if not exists"
        res = c.execute(text("""
            INSERT INTO emails
            (account_id, message_id, from_addr, to_addr, subject,
             category, confidence, reason, received_at, expires_at)
            SELECT
            :account_id, :message_id, :from_addr, :to_addr, :subject,
            :category, :confidence, :reason, now(), :expires_at
            WHERE NOT EXISTS (
                SELECT 1 FROM emails
                WHERE account_id = :account_id AND message_id = :message_id
            )
        """), mail)

        # res.rowcount = 1 => inserted, 0 => skipped
        return (res.rowcount or 0) > 0
