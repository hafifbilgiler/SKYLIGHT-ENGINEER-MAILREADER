from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

import requests
from urllib.parse import urlencode

from app.config import RETENTION_DAYS
from app.db.session import SessionLocal, engine
from app.db.models import Base, Account, Secret, Rule
from app.security.encryption import encrypt_payload, decrypt_payload


app = FastAPI(title="Skylight Engineer MailReader API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# IMAP ACCOUNT (user/pass)
# -------------------------
class ImapAccountCreate(BaseModel):
    email: str
    imap_host: str
    imap_port: int = 993
    username: str
    password: str = Field(..., min_length=1)


@app.post("/accounts/imap")
def create_imap_account(req: ImapAccountCreate):
    with SessionLocal() as db:
        exists = db.execute(select(Account).where(Account.email == req.email)).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=409, detail="Account already exists")

        acc = Account(auth_method="imap", email=req.email)
        db.add(acc)
        db.flush()

        payload = {
            "auth_method": "imap",
            "imap_host": req.imap_host,
            "imap_port": req.imap_port,
            "username": req.username,
            "password": req.password,  # encrypted in DB
        }
        sec = Secret(account_id=acc.id, enc_payload=encrypt_payload(payload))
        db.add(sec)

        # default rule: direct to me => important
        db.add(Rule(
            account_id=acc.id,
            name="direct_to_me",
            priority=100,
            enabled=True,
            conditions=[{"field": "to", "op": "icontains", "value": req.email}],
            action={"set_category": "important"},
        ))

        db.commit()
        return {
            "id": str(acc.id),
            "email": acc.email,
            "auth_method": acc.auth_method,
            "created_at": acc.created_at.isoformat(),
            "secret_stored": True
        }


# -----------------------------------------
# EXCHANGE OAUTH START (UI’dan client/tenant)
# -----------------------------------------
class ExchangeStart(BaseModel):
    email: str
    tenant_id: str
    client_id: str
    client_secret: str
    redirect_uri: str


@app.post("/accounts/exchange/start")
def exchange_start(req: ExchangeStart):
    """
    UI buraya tenant_id, client_id, client_secret, redirect_uri gönderir.
    Biz:
      - account + secret oluştururuz (refresh_token henüz yok)
      - auth_url döneriz
    """
    with SessionLocal() as db:
        exists = db.execute(select(Account).where(Account.email == req.email)).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=409, detail="Account already exists")

        acc = Account(auth_method="exchange", email=req.email)
        db.add(acc)
        db.flush()

        payload = {
            "auth_method": "exchange",
            "email": req.email,
            "tenant_id": req.tenant_id,
            "client_id": req.client_id,
            "client_secret": req.client_secret,
            "redirect_uri": req.redirect_uri,
            "refresh_token": ""
        }
        db.add(Secret(account_id=acc.id, enc_payload=encrypt_payload(payload)))

        # (opsiyonel) direct rule
        db.add(Rule(
            account_id=acc.id,
            name="direct_to_me",
            priority=100,
            enabled=True,
            conditions=[{"field": "to", "op": "icontains", "value": req.email}],
            action={"set_category": "important"},
        ))

        db.commit()

        auth_url = _build_ms_authorize_url(
            tenant_id=req.tenant_id,
            client_id=req.client_id,
            redirect_uri=req.redirect_uri,
            state=str(acc.id)  # state = account_id
        )

        return {
            "account_id": str(acc.id),
            "auth_url": auth_url
        }


def _build_ms_authorize_url(tenant_id: str, client_id: str, redirect_uri: str, state: str) -> str:
    base = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": "offline_access Mail.Read User.Read",
        "state": state
    }
    return f"{base}?{urlencode(params)}"


# -----------------------------------------
# OAUTH CALLBACK (Microsoft -> refresh_token)
# -----------------------------------------
@app.get("/oauth/microsoft/callback")
def microsoft_callback(code: str, state: str):
    """
    state = account_id (uuid string)
    code = Microsoft’un verdiği authorization code
    """
    with SessionLocal() as db:
        acc = db.execute(select(Account).where(Account.id == state)).scalar_one_or_none()
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        sec = db.execute(select(Secret).where(Secret.account_id == acc.id)).scalar_one_or_none()
        if not sec:
            raise HTTPException(status_code=404, detail="Secret not found")

        payload = decrypt_payload(sec.enc_payload)

        if payload.get("auth_method") != "exchange":
            raise HTTPException(status_code=400, detail="Account is not exchange type")

        tenant_id = payload["tenant_id"]
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": payload["client_id"],
            "client_secret": payload["client_secret"],
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": payload["redirect_uri"],
            "scope": "offline_access Mail.Read User.Read"
        }

        r = requests.post(token_url, data=data, timeout=30)
        if r.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {r.text}")

        token = r.json()
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token not returned (check offline_access + consent)")

        payload["refresh_token"] = refresh_token
        sec.enc_payload = encrypt_payload(payload)
        db.commit()

        return {"status": "ok", "message": "Exchange account connected"}


@app.get("/accounts")
def list_accounts():
    with SessionLocal() as db:
        rows = db.execute(select(Account)).scalars().all()
        return [
            {
                "id": str(a.id),
                "email": a.email,
                "auth_method": a.auth_method,
                "created_at": a.created_at.isoformat(),
                "has_secret": a.secret is not None,
            }
            for a in rows
        ]


@app.get("/retention")
def retention_info():
    return {"retention_days": RETENTION_DAYS, "policy": "emails are deleted after expires_at < now()"}
