from imapclient import IMAPClient


def fetch_imap_mails(host, username, password, port=993, limit=10):
    """
    Normalizes into:
      message_id, subject, from, body(empty)
    """
    mails = []

    with IMAPClient(host, port=port, ssl=True) as server:
        server.login(username, password)
        server.select_folder("INBOX")

        ids = server.search(["NOT", "DELETED"])
        ids = ids[-limit:] if ids else []

        if not ids:
            return []

        fetched = server.fetch(ids, ["ENVELOPE"])
        for _, msg in fetched.items():
            env = msg[b"ENVELOPE"]

            msg_id = env.message_id.decode() if env.message_id else ""
            subject = env.subject.decode(errors="ignore") if env.subject else ""

            from_addr = ""
            if env.from_ and len(env.from_) > 0:
                mb = env.from_[0].mailbox.decode(errors="ignore") if env.from_[0].mailbox else ""
                hs = env.from_[0].host.decode(errors="ignore") if env.from_[0].host else ""
                if mb and hs:
                    from_addr = f"{mb}@{hs}"

            mails.append({
                "message_id": msg_id,
                "subject": subject,
                "from": from_addr,
                "body": ""
            })

    return mails
