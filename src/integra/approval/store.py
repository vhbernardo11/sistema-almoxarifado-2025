from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .models import ApprovalRecord


class ApprovalStore(Protocol):
    def create(self, *, run_id: str, content_digest: str, metadata: dict[str, Any] | None = None) -> ApprovalRecord: ...
    def get(self, approval_id: str) -> ApprovalRecord: ...
    def decide(self, approval_id: str, *, decision: str, approver: str, note: str | None = None) -> ApprovalRecord: ...


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRecord] = {}

    def create(self, *, run_id: str, content_digest: str, metadata: dict[str, Any] | None = None) -> ApprovalRecord:
        item = ApprovalRecord(
            id=str(uuid4()),
            run_id=run_id,
            content_digest=content_digest,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.id] = item
        return deepcopy(item)

    def get(self, approval_id: str) -> ApprovalRecord:
        try:
            return deepcopy(self._items[approval_id])
        except KeyError as exc:
            raise KeyError(f"Approval {approval_id} não encontrada") from exc

    def decide(self, approval_id: str, *, decision: str, approver: str, note: str | None = None) -> ApprovalRecord:
        item = self.get(approval_id)
        if item.decision != "pending":
            raise ValueError("Uma aprovação decidida não pode ser alterada")
        item.decision = decision  # type: ignore[assignment]
        item.approver = approver
        item.note = note
        item.decided_at = datetime.now(timezone.utc)
        self._items[approval_id] = item
        return deepcopy(item)


class SupabaseApprovalStore:
    def __init__(self, client: Any):
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabaseApprovalStore":
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios no backend")
        from supabase import create_client
        return cls(create_client(url, key))

    @staticmethod
    def _one(response: Any) -> dict[str, Any]:
        data = getattr(response, "data", None)
        if data is None and isinstance(response, dict):
            data = response.get("data")
        rows = list(data or [])
        if not rows:
            raise KeyError("Registro de aprovação não encontrado")
        return rows[0]

    def create(self, *, run_id: str, content_digest: str, metadata: dict[str, Any] | None = None) -> ApprovalRecord:
        response = self.client.table("squad_approvals").insert({
            "run_id": run_id,
            "content_digest": content_digest,
            "metadata": metadata or {},
        }).execute()
        return ApprovalRecord.model_validate(self._one(response))

    def get(self, approval_id: str) -> ApprovalRecord:
        response = self.client.table("squad_approvals").select("*").eq("id", approval_id).limit(1).execute()
        return ApprovalRecord.model_validate(self._one(response))

    def decide(self, approval_id: str, *, decision: str, approver: str, note: str | None = None) -> ApprovalRecord:
        current = self.get(approval_id)
        if current.decision != "pending":
            raise ValueError("Uma aprovação decidida não pode ser alterada")
        response = self.client.table("squad_approvals").update({
            "decision": decision,
            "approver": approver,
            "note": note,
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval_id).execute()
        return ApprovalRecord.model_validate(self._one(response))
