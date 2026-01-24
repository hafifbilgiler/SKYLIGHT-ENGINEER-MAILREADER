import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

MAILREADER_API_URL = os.environ.get(
    "MAILREADER_API_URL",
    "http://skylight-engineer-mailreader-api:8000"
)

app = FastAPI(title="Skylight Engineer MailReader UI")

# =========================
# STATIC UI
# =========================
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# =========================
# ENV → JS (RUNTIME)
# =========================
@app.get("/env.js")
def env_js():
    js = """
    window.RUNTIME_CONFIG = {
        API_BASE: ""
    };
    """
    return Response(js, media_type="application/javascript")


# =========================
# BFF – API PASSTHROUGH
# =========================

def proxy_response(r: requests.Response):
    """
    Ortak response handler
    """
    try:
        return JSONResponse(
            status_code=r.status_code,
            content=r.json()
        )
    except Exception:
        return JSONResponse(
            status_code=r.status_code,
            content={"detail": r.text}
        )


# -------- ACCOUNTS --------

@app.get("/accounts")
def get_accounts():
    r = requests.get(f"{MAILREADER_API_URL}/accounts", timeout=10)
    return proxy_response(r)

@app.delete("/accounts/{account_id}")
def delete_account(account_id: str):
    r = requests.delete(
        f"{MAILREADER_API_URL}/accounts/{account_id}",
        timeout=10
    )
    return proxy_response(r)

@app.post("/accounts/imap")
async def create_account(req: Request):
    payload = await req.json()
    r = requests.post(
        f"{MAILREADER_API_URL}/accounts/imap",
        json=payload,
        timeout=10
    )
    return proxy_response(r)


# -------- RULES --------

@app.get("/rules")
def get_rules(account_id: str):
    r = requests.get(
        f"{MAILREADER_API_URL}/rules",
        params={"account_id": account_id},
        timeout=10
    )
    return proxy_response(r)


@app.post("/rules")
async def create_rule(req: Request):
    payload = await req.json()
    r = requests.post(
        f"{MAILREADER_API_URL}/rules",
        json=payload,
        timeout=10
    )
    return proxy_response(r)


# -------- EMAILS (🔥 ASIL EKSİK BUYDU) --------

@app.get("/emails")
def list_emails(
    account_id: str,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0
):
    params = {
        "account_id": account_id,
        "limit": limit,
        "offset": offset
    }
    if category:
        params["category"] = category

    r = requests.get(
        f"{MAILREADER_API_URL}/emails",
        params=params,
        timeout=15
    )
    return proxy_response(r)


@app.get("/emails/important")
def important_emails(account_id: str, limit: int = 20):
    r = requests.get(
        f"{MAILREADER_API_URL}/emails/important",
        params={
            "account_id": account_id,
            "limit": limit
        },
        timeout=10
    )
    return proxy_response(r)


@app.get("/emails/latest")
def latest_email(account_id: str):
    r = requests.get(
        f"{MAILREADER_API_URL}/emails/latest",
        params={"account_id": account_id},
        timeout=10
    )
    return proxy_response(r)
