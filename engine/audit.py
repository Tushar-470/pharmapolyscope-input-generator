"""
Audit trail logging and compliance engine.
Records immutable timestamps, previous values, new values, user actions, and recalculation reasons.
"""

import os
import json
import datetime
import logging
from typing import Dict, Any, List, Optional


class AuditTrailEngine:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_path = os.path.join(base_dir, "data", "store", "audit_trail.json")
        self.storage_path = storage_path
        self._ensure_store_exists()

    def _ensure_store_exists(self):
        if not os.path.exists(self.storage_path):
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"audit_version": "1.0", "events": []}, f, indent=2)

    def log_event(
        self,
        entity_id: str,
        entity_name: str,
        action: str,
        user: str = "Scientist / User",
        reason: str = "Property generation / recalculation",
        field_changes: Optional[List[Dict[str, Any]]] = None,
        method_version: str = "input-generator/1.0"
    ) -> Dict[str, Any]:
        """
        Appends an event to the audit log.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        event = {
            "timestamp": timestamp,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "action": action,
            "user": user,
            "method_version": method_version,
            "field_changes": field_changes if field_changes is not None else [],
            "reason": reason
        }
        
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("events", []).append(event)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Audit log warning: {e}")
            
        return event

    def get_events(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves audit trail events, optionally filtered by entity_id."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = data.get("events", [])
            if entity_id:
                return [e for e in events if e.get("entity_id") == entity_id]
            return events
        except Exception:
            return []
