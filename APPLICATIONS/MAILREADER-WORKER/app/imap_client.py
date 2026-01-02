from imapclient import IMAPClient

def fetch_imap_mails(host, username, password, port=993, limit=10):
    mails = []

    with IMAPClient(host, port=port, ssl=True) as server:
        server.login(username, password)
        server.select_folder("INBOX")
        ids = server.search(["NOT", "DELETED"])[-limit:]

        for uid, msg in server.fetch(ids, ["ENVELOPE"]).items():
            env = msg[b"ENVELOPE"]
            mails.append({
                "message_id": env.message_id.decode() if env.message_id else "",
                "subject": env.subject.decode() if env.subject else "",
                "from": env.from_[0].mailbox.decode() + "@" + env.from_[0].host.decode(),
            })

    return mails
