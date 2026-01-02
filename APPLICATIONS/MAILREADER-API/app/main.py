from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.db.session import SessionLocal, engine
from app.db.models import Base, Account, Secret, Rule
from app.security.encryption import encrypt_payload
from app.config import RETENTION_DAYS
from app.llm_client import completion

app = FastAPI(title="Skylight Engineer MailReader API")

@app.on_event("startup")
def on_startup():
    # MVP: schema auto create
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

class ImapAccountCreate(BaseModel):
    email: str
    imap_host: str
    imap_port: int = 993
    username: str
    password: str = Field(..., min_length=1)

@app.post("/accounts/imap")
def create_imap_account(req: ImapAccountCreate):
    with SessionLocal() as db:
        # unique email check
        exists = db.execute(select(Account).where(Account.email == req.email)).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=409, detail="Account already exists")

        acc = Account(provider="imap", email=req.email)
        db.add(acc)
        db.flush()  # acc.id

        payload = {
            "imap_host": req.imap_host,
            "imap_port": req.imap_port,
            "username": req.username,
            "password": req.password,  # encrypted in DB
        }
        enc = encrypt_payload(payload)
        sec = Secret(account_id=acc.id, enc_payload=enc)
        db.add(sec)

        # default basic rules (örnek)
        default_rule_direct = Rule(
            account_id=acc.id,
            name="direct_to_me",
            priority=100,
            enabled=True,
            conditions=[{"field": "to", "op": "icontains", "value": req.email}],
            action={"set_category": "important"},
        )
        db.add(default_rule_direct)

        db.commit()

        # password asla dönmez
        return {
            "id": str(acc.id),
            "email": acc.email,
            "provider": acc.provider,
            "created_at": acc.created_at.isoformat(),
            "secret_stored": True
        }

@app.get("/accounts")
def list_accounts():
    with SessionLocal() as db:
        rows = db.execute(select(Account)).scalars().all()
        return [
            {
                "id": str(a.id),
                "email": a.email,
                "provider": a.provider,
                "created_at": a.created_at.isoformat(),
                "has_secret": a.secret is not None,
            }
            for a in rows
        ]

class RuleCreate(BaseModel):
    account_email: str
    name: str
    priority: int = 50
    enabled: bool = True
    conditions: list
    action: dict

@app.post("/rules")
def create_rule(req: RuleCreate):
    with SessionLocal() as db:
        acc = db.execute(select(Account).where(Account.email == req.account_email)).scalar_one_or_none()
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        r = Rule(
            account_id=acc.id,
            name=req.name,
            priority=req.priority,
            enabled=req.enabled,
            conditions=req.conditions,
            action=req.action,
        )
        db.add(r)
        db.commit()
        return {"id": str(r.id), "name": r.name, "priority": r.priority, "enabled": r.enabled}

@app.get("/rules")
def list_rules(account_email: str):
    with SessionLocal() as db:
        acc = db.execute(select(Account).where(Account.email == account_email)).scalar_one_or_none()
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        rules = db.execute(select(Rule).where(Rule.account_id == acc.id).order_by(Rule.priority.desc())).scalars().all()
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "priority": r.priority,
                "enabled": r.enabled,
                "conditions": r.conditions,
                "action": r.action,
            }
            for r in rules
        ]

# LLM ping (opsiyonel)
class PingReq(BaseModel):
    text: str = "Return ONLY the word OK."

@app.post("/llm/ping")
def llm_ping(req: PingReq):
    out = completion(req.text, temperature=0.0, max_tokens=8)
    return {"model_reply": out}

@app.get("/retention")
def retention_info():
    return {"retention_days": RETENTION_DAYS, "policy": "emails are deleted after expires_at < now()"}
