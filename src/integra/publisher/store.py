from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .models import PublicationReceipt, PublicationRecord


class PublicationStore(Protocol):
    def create_prepared(self, *, run_id: str, approval_id: str, provider: str, target: dict[str, Any]) -> PublicationRecord: ...
    def mark_succeeded(self, publication_id: str, receipt: PublicationReceipt) -> PublicationRecord: ...
    def mark_failed(self, publication_id: str, error: str) -> PublicationRecord: ...


class InMemoryPublicationStore:
    def __init__(self) -> None:
        self._items: dict[str, PublicationRecord] = {}

    def create_prepared(self, *, run_id: str, approval_id: str, provider: str, target: dict[str, Any]) -> PublicationRecord:
        item = PublicationRecord(
            id=str(uuid4()), run_id=run_id, approval_id=approval_id, provider=provider,
            target=deepcopy(target), status="prepared", created_at=datetime.now(timezone.utc)
        )
        self._items[item.id] = item
        return deepcopy(item)

    def mark_succeeded(self, publication_id: str, receipt: PublicationReceipt) -> PublicationRecord:
        item = deepcopy(self._items[publication_id])
        item.status = receipt.status
        item.external_id = receipt.external_id
        item.planner_url = str(receipt.planner_url) if receipt.planner_url else None
        item.attempted_at = receipt.executed_at or datetime.now(timezone.utc)
        item.error = None
        self._items[publication_id] = item
        return deepcopy(item)

    def mark_failed(self, publication_id: str, error: str) -> PublicationRecord:
        item = deepcopy(self._items[publication_id])
        item.status = "failed"
        item.error = error
        item.attempted_at = datetime.now(timezone.utc)
        self._items[publication_id] = item
        return deepcopy(item)


class SupabasePublicationStore:
    def __init__(self, client: Any):
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabasePublicationStore":
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
            raise KeyError("Registro de publicação não encontrado")
        return rows[0]

    def create_prepared(self, *, run_id: str, approval_id: str, provider: str, target: dict[str, Any]) -> PublicationRecord:
        response = self.client.table("squad_publications").insert({
            "run_id": run_id,
            "approval_id": approval_id,
            "provider": provider,
            "target": target,
            "status": "prepared",
        }).execute()
        return PublicationRecord.model_validate(self._one(response))

    def mark_succeeded(self, publication_id: str, receipt: PublicationReceipt) -> PublicationRecord:
        response = self.client.table("squad_publications").update({
            "status": receipt.status,
            "external_id": receipt.external_id,
            "planner_url": str(receipt.planner_url) if receipt.planner_url else None,
            "attempted_at": (receipt.executed_at or datetime.now(timezone.utc)).isoformat(),
            "error": None,
        }).eq("id", publication_id).execute()
        return PublicationRecord.model_validate(self._one(response))

    def mark_failed(self, publication_id: str, error: str) -> PublicationRecord:
        response = self.client.table("squad_publications").update({
            "status": "failed",
            "error": error,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", publication_id).execute()
        return PublicationRecord.model_validate(self._one(response))
