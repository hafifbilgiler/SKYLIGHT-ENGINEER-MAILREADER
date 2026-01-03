from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
import uuid

from app.db.session import SessionLocal
from app.db.models import Rule

router = APIRouter(prefix="/rules", tags=["rules"])

# ================== SCHEMA ==================

class RuleCreate(BaseModel):
    account_id: uuid.UUID
    name: str
    field: str            # subject | from | to | body
    contains: str
    action: str           # important | spam
    priority: int = 50
    enabled: bool = True


# ================== API ==================

@router.post("")
def create_rule(req: RuleCreate):
    with SessionLocal() as db:
        rule = Rule(
            account_id=req.account_id,
            name=req.name,
            priority=req.priority,
            enabled=req.enabled,
            conditions=[
                {
                    "field": req.field,
                    "op": "contains",
                    "value": req.contains
                }
            ],
            action={
                "set_category": req.action
            }
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return {"id": str(rule.id)}


@router.get("")
def list_rules(account_id: uuid.UUID):
    with SessionLocal() as db:
        rules = db.execute(
            select(Rule)
            .where(Rule.account_id == account_id)
            .order_by(Rule.priority.desc())
        ).scalars().all()

        result = []
        for r in rules:
            cond = r.conditions[0] if r.conditions else {}
            result.append({
                "id": str(r.id),
                "name": r.name,
                "priority": r.priority,
                "enabled": r.enabled,
                "field": cond.get("field"),
                "contains": cond.get("value"),
                "action": r.action.get("set_category")
            })

        return result


@router.delete("/{rule_id}")
def delete_rule(rule_id: uuid.UUID):
    with SessionLocal() as db:
        rule = db.get(Rule, rule_id)
        if not rule:
            raise HTTPException(404, "Rule not found")
        db.delete(rule)
        db.commit()
        return {"status": "deleted"}
