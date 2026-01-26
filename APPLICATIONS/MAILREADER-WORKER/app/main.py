import os
import time
import logging
from datetime import datetime, timedelta

from app.db import get_accounts, get_rules, insert_email, update_secret_payload
from app.rule_engine import apply_rules
from app.llm_classifier import classify
from app.security import decrypt_payload, encrypt_payload

from app.graph_client import refresh_access_token, fetch_graph_mails
from app.imap_client import fetch_imap_mails

# ========================== CONFIG ==========================
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "10"))
FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "3"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

def INTRO():
    logging.info("EIGHT - SKYLIGHT MAILREADER WORKER (SERVICE MODE)")

# ========================== CORE ==========================
def process_account(acc: dict):
    rules = get_rules(acc["id"])

    secrets = decrypt_payload(acc["enc_payload"])
    auth_method = (acc.get("auth_method") or secrets.get("auth_method") or "imap").lower()

    mails = []

    # -------- EXCHANGE --------
    if auth_method == "exchange":
        tenant_id = secrets.get("tenant_id", "")
        client_id = secrets.get("client_id", "")
        client_secret = secrets.get("client_secret", "")
        refresh_token = secrets.get("refresh_token", "")

        if not (tenant_id and client_id and client_secret and refresh_token):
            logging.warning(f"EXCHANGE CONFIG MISSING for {acc['email']}")
            return

        token_json = refresh_access_token(
            tenant_id, client_id, client_secret, refresh_token
        )
        access_token = token_json.get("access_token", "")

        new_refresh = token_json.get("refresh_token")
        if new_refresh and new_refresh != refresh_token:
            secrets["refresh_token"] = new_refresh
            update_secret_payload(acc["id"], encrypt_payload(secrets))
            logging.info(f"REFRESH TOKEN UPDATED for {acc['email']}")

        mails = fetch_graph_mails(access_token, limit=FETCH_LIMIT)

        for m in mails:
            m.setdefault("to", acc["email"])
            m.setdefault("body", "")

    # -------- IMAP --------
    elif auth_method == "imap":
        host = secrets.get("imap_host", "")
        username = secrets.get("username", "")
        password = secrets.get("password", "")
        port = int(secrets.get("imap_port", 993))

        if not (host and username and password):
            logging.warning(f"IMAP CONFIG MISSING for {acc['email']}")
            return

        mails = fetch_imap_mails(
            host=host,
            username=username,
            password=password,
            port=port,
            limit=FETCH_LIMIT
        )

        for m in mails:
            m["to"] = acc["email"]
            m.setdefault("body", "")

    else:
        logging.warning(f"UNKNOWN auth_method={auth_method} for {acc['email']}")
        return

    if not mails:
        logging.info(f"NO MAILS for {acc['email']}")
        return

    # ================== MAIL PIPELINE ==================
    for m in mails:
        # 1️⃣ RULE ENGINE (ÖNCE)
        action, rule_name = apply_rules(m, rules)

        if action:
            category = (action.get("set_category") or "normal").lower()
            confidence = 90
            reason = f"rule:{rule_name}"

        else:
            # 2️⃣ LLM CLASSIFIER (🔥 ASIL AKIL BURADA)
            category, confidence, reason = classify(m)

            logging.info(
                f"LLM classified | {acc['email']} | {m.get('subject','')[:40]} → {category} ({confidence})"
            )

        mail_row = {
            "account_id": acc["id"],
            "message_id": m.get("message_id", "") or "",
            "from_addr": m.get("from", "") or "",
            "to_addr": m.get("to", "") or "",
            "subject": m.get("subject", "") or "",
            "category": category,
            "confidence": int(confidence),
            "reason": (reason or "")[:255],
            "expires_at": datetime.utcnow() + timedelta(days=RETENTION_DAYS),
        }

        inserted = insert_email(mail_row)
        if inserted:
            logging.info(
                f"INSERTED {category.upper()} - {acc['email']} - {mail_row['subject'][:60]}"
            )
        else:
            logging.info(
                f"SKIPPED (DUP/EMPTY) - {acc['email']} - {mail_row['subject'][:60]}"
            )

def run_once():
    accounts = get_accounts()
    if not accounts:
        logging.info("NO ACCOUNTS FOUND")
        return

    for acc in accounts:
        try:
            process_account(acc)
        except Exception as e:
            logging.error(f"ACCOUNT ERROR {acc.get('email')}: {e}")

def service_loop():
    INTRO()
    while True:
        try:
            run_once()
        except Exception as e:
            logging.error(f"RUN ERROR: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    service_loop()
