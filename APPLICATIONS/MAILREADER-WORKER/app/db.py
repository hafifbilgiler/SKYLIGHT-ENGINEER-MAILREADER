import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_accounts():
    with engine.connect() as c:
        return c.execute(text("""
            SELECT a.id, a.email, a.auth_method, s.enc_payload
            FROM accounts a
            JOIN secrets s ON s.account_id = a.id
        """)).mappings().all()

def get_rules(account_id):
    with engine.connect() as c:
        return c.execute(text("""
            SELECT name, priority, conditions, action
            FROM rules
            WHERE account_id = :aid AND enabled = true
            ORDER BY priority DESC
        """), {"aid": account_id}).mappings().all()

def insert_email(account_id, mail):
    with engine.connect() as c:
        c.execute(text("""
            INSERT INTO emails
            (account_id, message_id, from_addr, to_addr, subject,
             category, confidence, reason, received_at, expires_at)
            VALUES
            (:account_id, :message_id, :from_addr, :to_addr, :subject,
             :category, :confidence, :reason, now(), :expires_at)
        """), mail)
        c.commit()
