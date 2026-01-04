from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.models import Email
from datetime import datetime

router = APIRouter(prefix="/emails", tags=["emails"])


# =========================================================
# LIST EMAILS (GENEL LİSTE)
# =========================================================
@router.get("")
@router.get("/")
def list_emails(
    account_id: str,
    category: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
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
                "received_at": e.received_at.isoformat(),
            }
            for e in rows
        ]


# =========================================================
# IMPORTANT EMAILS (DASHBOARD / UI KARTLARI İÇİN)
# =========================================================
@router.get("/important")
def important_emails(
    account_id: str,
    limit: int = Query(20, ge=1, le=100)
):
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
                "received_at": e.received_at.isoformat(),
            }
            for e in rows
        ]


# =========================================================
# LATEST EMAIL (HEADER / WIDGET İÇİN)
# =========================================================
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
            "id": str(e.id),
            "from": e.from_addr,
            "subject": e.subject,
            "category": e.category,
            "confidence": e.confidence,
            "reason": e.reason,
            "received_at": e.received_at.isoformat(),
        }


# =========================================================
# EMAIL COUNT (UI BADGE / STAT)
# =========================================================
@router.get("/count")
def email_count(
    account_id: str,
    category: str | None = None
):
    with SessionLocal() as db:
        q = select(func.count()).select_from(Email).where(
            Email.account_id == account_id
        )

        if category:
            q = q.where(Email.category == category)

        total = db.execute(q).scalar()

        return {
            "account_id": account_id,
            "category": category,
            "count": total,
        }
