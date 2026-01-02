import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

def fetch_graph_mails(access_token, limit=10):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_BASE}/me/mailFolders/Inbox/messages?$top={limit}"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])
