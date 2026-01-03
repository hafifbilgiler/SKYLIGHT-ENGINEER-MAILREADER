import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from app.db import get_accounts, get_rules, insert_email
from app.rule_engine import apply_rules
from app.llm_classifier import classify
from app.security import decrypt_payload

from app.graph_client import refresh_access_token, fetch_graph_mails
from app.imap_client import fetch_imap_mails


def run():
    accounts = get_accounts()
    for acc in accounts:
        rules = get_rules(acc["id"])
        secrets = decrypt_payload(acc["enc_payload"])  # decrypted dict

        auth_method = acc["auth_method"]

        if auth_method == "exchange":
            if not secrets.get("refresh_token"):
                # henüz connect edilmemiş
                continue

            access_token = refresh_access_token(
                tenant_id=secrets["tenant_id"],
                client_id=secrets["client_id"],
                client_secret=secrets["client_secret"],
                refresh_token=secrets["refresh_token"]
            )
            items = fetch_graph_mails(access_token, limit=10)

            mails = []
            for m in items:
                mails.append({
                    "message_id": m.get("internetMessageId", "") or m.get("id", ""),
                    "subject": m.get("subject", "") or "",
                    "from": (m.get("from", {}) or {}).get("emailAddress", {}).get("address", "") or "",
                    "to": acc["email"],
                    "body": m.get("bodyPreview", "") or ""
                })

        elif auth_method == "imap":
            mails = fetch_imap_mails(
                host=secrets["imap_host"],
                username=secrets["username"],
                password=secrets["password"],
                port=int(secrets.get("imap_port", 993)),
                limit=10
            )
            # normalize
            for m in mails:
                m["to"] = acc["email"]
                m.setdefault("body", "")

        else:
            continue

        for m in mails:
            action, rule_name = apply_rules(m, rules)

            if action:
                category = action.get("set_category", "normal")
                confidence = 90
                reason = f"rule:{rule_name}"
            else:
                category = classify(m)
                confidence = 70
                reason = "llm"

            insert_email(acc["id"], {
                "account_id": acc["id"],
                "message_id": m.get("message_id", ""),
                "from_addr": m.get("from", ""),
                "to_addr": m.get("to", ""),
                "subject": m.get("subject", ""),
                "category": category,
                "confidence": confidence,
                "reason": reason,
                "expires_at": datetime.utcnow() + timedelta(days=3),
            })


if __name__ == "__main__":
    run()
