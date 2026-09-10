from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import ApprovalRecord
from .store import ApprovalStore


class ApprovalError(RuntimeError):
    pass


def canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ApprovalGate:
    def __init__(self, store: ApprovalStore):
        self.store = store

    def request_approval(self, *, run_id: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> ApprovalRecord:
        return self.store.create(run_id=run_id, content_digest=canonical_digest(payload), metadata=metadata)

    def decide(self, approval_id: str, *, decision: str, approver: str, note: str | None = None) -> ApprovalRecord:
        if decision not in {"approved", "changes_requested", "rejected"}:
            raise ApprovalError("Decisão inválida")
        return self.store.decide(approval_id, decision=decision, approver=approver, note=note)

    def validate_for_publication(self, *, approval_id: str, run_id: str, payload: dict[str, Any]) -> ApprovalRecord:
        approval = self.store.get(approval_id)
        if approval.run_id != run_id:
            raise ApprovalError("A aprovação não pertence a esta execução")
        if approval.decision != "approved":
            raise ApprovalError("Publicação bloqueada: aprovação humana ausente")
        if approval.content_digest != canonical_digest(payload):
            raise ApprovalError("Publicação bloqueada: o conteúdo mudou depois da aprovação")
        return approval
