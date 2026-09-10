from __future__ import annotations

from typing import Any, Protocol

from integra.approval.gate import ApprovalGate

from .models import PublicationReceipt, PublisherResult
from .store import PublicationStore


class PublisherError(RuntimeError):
    pass


class PublisherAdapter(Protocol):
    def publish(self, payload: dict[str, Any]) -> PublicationReceipt: ...


class PublisherService:
    """Portão final antes de qualquer integração externa."""

    def __init__(
        self,
        approval_gate: ApprovalGate,
        adapter: PublisherAdapter | None = None,
        publication_store: PublicationStore | None = None,
        provider: str = "metricool",
    ):
        self.approval_gate = approval_gate
        self.adapter = adapter
        self.publication_store = publication_store
        self.provider = provider

    def prepare(self, *, run_id: str, approval_id: str, payload: dict[str, Any]) -> PublisherResult:
        self.approval_gate.validate_for_publication(approval_id=approval_id, run_id=run_id, payload=payload)
        publication_id = None
        if self.publication_store is not None:
            record = self.publication_store.create_prepared(
                run_id=run_id, approval_id=approval_id, provider=self.provider, target=payload
            )
            publication_id = record.id
        return PublisherResult(
            run_id=run_id,
            approval_id=approval_id,
            publication_id=publication_id,
            ready=True,
        )

    def publish(
        self,
        *,
        run_id: str,
        approval_id: str,
        payload: dict[str, Any],
        execution_authorized: bool = False,
    ) -> PublisherResult:
        prepared = self.prepare(run_id=run_id, approval_id=approval_id, payload=payload)
        if not execution_authorized:
            raise PublisherError("Publicação bloqueada: falta autorização explícita de execução")
        if self.adapter is None:
            raise PublisherError("Publisher externo não configurado")

        try:
            receipt = self.adapter.publish(payload)
        except Exception as exc:
            if prepared.publication_id and self.publication_store is not None:
                self.publication_store.mark_failed(prepared.publication_id, str(exc))
            raise

        if prepared.publication_id and self.publication_store is not None:
            self.publication_store.mark_succeeded(prepared.publication_id, receipt)

        return prepared.model_copy(update={
            "publication_attempted": True,
            "external_actions_performed": True,
            "receipt": receipt,
        })
