import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from app.db import get_accounts, get_rules, insert_email
from app.graph_client import fetch_graph_mails
from app.imap_client import fetch_imap_mails
from app.rule_engine import apply_rules
from app.llm_classifier import classify

MASTER_KEY = Fernet(
    json.loads(f'"{__import__("os").getenv("MAILREADER_MASTER_KEY")}"')
)

def decrypt(payload):
    return json.loads(MASTER_KEY.decrypt(payload.encode()).decode())

def run():
    accounts = get_accounts()

    for acc in accounts:
        rules = get_rules(acc["id"])
        secrets = decrypt(acc["enc_payload"])

        if acc["auth_method"] == "exchange":
            mails = fetch_graph_mails(secrets["access_token"])

        elif acc["auth_method"] == "imap":
            mails = fetch_imap_mails(
                secrets["imap_host"],
                secrets["username"],
                secrets["password"],
                secrets.get("imap_port", 993)
            )
        else:
            continue

        for m in mails:
            action, rule_name = apply_rules(m, rules)

            if action:
                category = action["set_category"]
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
                "to_addr": acc["email"],
                "subject": m.get("subject", ""),
                "category": category,
                "confidence": confidence,
                "reason": reason,
                "expires_at": datetime.utcnow() + timedelta(days=3)
            })

if __name__ == "__main__":
    run()
