import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def refresh_access_token(tenant_id: str, client_id: str, client_secret: str, refresh_token: str) -> str:
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "Mail.Read User.Read"
    }
    r = requests.post(token_url, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def fetch_graph_mails(access_token: str, limit: int = 10):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_BASE}/me/mailFolders/Inbox/messages?$top={limit}"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])
