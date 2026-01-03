from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Email
from datetime import datetime

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
def list_emails(
    account_id: str,
    category: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    with SessionLocal() as db:
        q = select(Email).where(Email.account_id == account_id)

        if category:
            q = q.where(Email.category == category)

        q = q.order_by(Email.received_at.desc()).limit(limit).offset(offset)
        rows = db.execute(q).scalars().all()

        return [
            {
                "id": str(e.id),
                "from": e.from_addr,
                "to": e.to_addr,
                "subject": e.subject,
                "category": e.category,
                "confidence": e.confidence,
                "reason": e.reason,
                "received_at": e.received_at.isoformat()
            }
            for e in rows
        ]


@router.get("/important")
def important_emails(account_id: str, limit: int = 20):
    with SessionLocal() as db:
        q = (
            select(Email)
            .where(Email.account_id == account_id)
            .where(Email.category == "important")
            .order_by(Email.received_at.desc())
            .limit(limit)
        )
        rows = db.execute(q).scalars().all()

        return [
            {
                "id": str(e.id),
                "from": e.from_addr,
                "subject": e.subject,
                "confidence": e.confidence,
                "received_at": e.received_at.isoformat()
            }
            for e in rows
        ]


@router.get("/latest")
def latest_email(account_id: str):
    with SessionLocal() as db:
        q = (
            select(Email)
            .where(Email.account_id == account_id)
            .order_by(Email.received_at.desc())
            .limit(1)
        )
        e = db.execute(q).scalar_one_or_none()

        if not e:
            return None

        return {
            "from": e.from_addr,
            "subject": e.subject,
            "category": e.category,
            "confidence": e.confidence,
            "received_at": e.received_at.isoformat()
        }
