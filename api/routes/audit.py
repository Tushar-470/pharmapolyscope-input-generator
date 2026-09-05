"""
Audit log API routes.
"""

from fastapi import APIRouter
from typing import Optional
from engine.audit import AuditTrailEngine

router = APIRouter(prefix="/api/audit", tags=["audit"])

audit_engine = AuditTrailEngine()


@router.get("")
def get_audit_logs(entity_id: Optional[str] = None):
    """Retrieves all logged audit events, optionally filtered by entity_id."""
    events = audit_engine.get_events(entity_id)
    return {"events": events, "count": len(events)}
