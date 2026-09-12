from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import WorkflowReview


class ReviewError(RuntimeError):
    pass


def canonical_review_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ReviewCenter:
    """Fila de revisão humana da Etapa 15, deliberadamente separada do Publisher."""

    def __init__(self) -> None:
        self._items: dict[str, WorkflowReview] = {}
        self._by_job: dict[str, str] = {}

    @staticmethod
    def _guard_actor(actor_id: str) -> None:
        if not actor_id.startswith("stage8-test-"):
            raise ReviewError("Etapa 15 aceita somente atores sintéticos stage8-test-*.")

    def create(
        self,
        *,
        job_id: str,
        actor_id: str,
        route: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowReview:
        self._guard_actor(actor_id)
        existing_id = self._by_job.get(job_id)
        if existing_id:
            existing = self._items[existing_id]
            if existing.payload_digest != canonical_review_digest(payload):
                raise ReviewError("O mesmo job não pode trocar de conteúdo depois de entrar em revisão.")
            return deepcopy(existing)
        item = WorkflowReview(
            id=str(uuid4()),
            job_id=job_id,
            test_actor_id=actor_id,
            route=route,
            payload_digest=canonical_review_digest(payload),
            review_payload=deepcopy(payload),
            metadata=deepcopy(metadata or {}),
            publication_authorized=False,
            external_actions_authorized=False,
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.id] = item
        self._by_job[job_id] = item.id
        return deepcopy(item)

    def get(self, review_id: str) -> WorkflowReview:
        try:
            return deepcopy(self._items[review_id])
        except KeyError as exc:
            raise ReviewError(f"Revisão desconhecida: {review_id}") from exc

    def decide(
        self,
        review_id: str,
        *,
        decision: str,
        reviewer: str,
        note: str | None = None,
    ) -> WorkflowReview:
        if decision not in {"accepted", "changes_requested", "rejected"}:
            raise ReviewError("Decisão de revisão inválida.")
        if not reviewer.startswith("stage8-test-admin-"):
            raise ReviewError("A decisão de homologação exige reviewer sintético stage8-test-admin-*.")
        item = self.get(review_id)
        if item.decision != "pending":
            raise ReviewError("Uma revisão já decidida não pode ser alterada.")
        item.decision = decision  # type: ignore[assignment]
        item.reviewer = reviewer
        item.note = note
        item.decided_at = datetime.now(timezone.utc)
        item.publication_authorized = False
        item.external_actions_authorized = False
        self._items[review_id] = item
        return deepcopy(item)

    def validate_payload(self, review_id: str, payload: dict[str, Any]) -> WorkflowReview:
        item = self.get(review_id)
        if item.payload_digest != canonical_review_digest(payload):
            raise ReviewError("O conteúdo mudou depois que entrou na fila de revisão.")
        if item.publication_authorized or item.external_actions_authorized:
            raise ReviewError("Revisão da Etapa 15 nunca autoriza efeito externo.")
        return item
