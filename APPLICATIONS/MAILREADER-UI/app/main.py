import os
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

MAILREADER_API_URL = os.environ.get(
    "MAILREADER_API_URL",
    "http://mailreader-api:8000"
)

app = FastAPI(title="Skylight Engineer MailReader UI")

# Static HTML
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r") as f:
        return f.read()


# 🔥 ENV → JS (RUNTIME)
@app.get("/env.js")
def env_js():
    js = f"""
    window.RUNTIME_CONFIG = {{
        API_BASE: ""
    }};
    """
    return Response(js, media_type="application/javascript")


# =========================
# BFF – API PASSTHROUGH
# =========================

@app.get("/accounts")
def get_accounts():
    r = requests.get(f"{MAILREADER_API_URL}/accounts", timeout=10)
    return r.json()


@app.post("/accounts/imap")
def create_account(payload: dict):
    r = requests.post(
        f"{MAILREADER_API_URL}/accounts/imap",
        json=payload,
        timeout=10
    )
    return r.json()


@app.get("/rules")
def get_rules(account_id: str):
    r = requests.get(
        f"{MAILREADER_API_URL}/rules",
        params={"account_id": account_id},
        timeout=10
    )
    return r.json()


@app.post("/rules")
def create_rule(payload: dict):
    r = requests.post(
        f"{MAILREADER_API_URL}/rules",
        json=payload,
        timeout=10
    )
    return r.json()
