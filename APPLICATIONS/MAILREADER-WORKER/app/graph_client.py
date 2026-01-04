import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def refresh_access_token(tenant_id: str, client_id: str, client_secret: str, refresh_token: str) -> dict:
    """
    Returns token json (at least access_token; may also include refresh_token).
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "offline_access Mail.Read User.Read"
    }
    r = requests.post(token_url, data=data, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_graph_mails(access_token: str, limit: int = 10):
    """
    Normalizes into:
      message_id, subject, from, to, body
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_BASE}/me/mailFolders/Inbox/messages?$top={limit}&$select=id,subject,from,toRecipients,bodyPreview,internetMessageId"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    items = r.json().get("value", []) or []

    out = []
    for m in items:
        from_addr = ""
        try:
            from_addr = m.get("from", {}).get("emailAddress", {}).get("address", "") or ""
        except Exception:
            from_addr = ""

        to_addr = ""
        try:
            rec = (m.get("toRecipients") or [])
            if rec:
                to_addr = rec[0].get("emailAddress", {}).get("address", "") or ""
        except Exception:
            to_addr = ""

        out.append({
            "message_id": (m.get("internetMessageId") or m.get("id") or ""),
            "subject": (m.get("subject") or ""),
            "from": from_addr,
            "to": to_addr,
            "body": (m.get("bodyPreview") or "")
        })

    return out
