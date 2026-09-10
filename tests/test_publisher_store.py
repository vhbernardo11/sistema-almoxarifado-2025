from __future__ import annotations

from datetime import datetime, timezone

import pytest

from integra.approval import ApprovalGate, InMemoryApprovalStore
from integra.publisher import (
    InMemoryPublicationStore,
    PublicationReceipt,
    PublisherError,
    PublisherService,
)

PAYLOAD = {"network": "instagram", "text": "Conheça", "media": ["https://example.org/post.png"]}


def approved_gate():
    gate = ApprovalGate(InMemoryApprovalStore())
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    return gate, approval


def test_prepare_persists_only_prepared_record_without_external_action():
    gate, approval = approved_gate()
    store = InMemoryPublicationStore()
    result = PublisherService(gate, publication_store=store).prepare(
        run_id="run-1", approval_id=approval.id, payload=PAYLOAD
    )
    assert result.ready is True
    assert result.publication_id is not None
    assert result.external_actions_performed is False
    assert store._items[result.publication_id].status == "prepared"


def test_success_is_persisted_only_after_explicit_execution_authorization():
    class FakeAdapter:
        def publish(self, payload):
            return PublicationReceipt(
                provider="fake", external_id="ext-1", status="scheduled", executed_at=datetime.now(timezone.utc)
            )

    gate, approval = approved_gate()
    store = InMemoryPublicationStore()
    service = PublisherService(gate, adapter=FakeAdapter(), publication_store=store, provider="fake")
    with pytest.raises(PublisherError):
        service.publish(run_id="run-1", approval_id=approval.id, payload=PAYLOAD)

    result = service.publish(
        run_id="run-1", approval_id=approval.id, payload=PAYLOAD, execution_authorized=True
    )
    assert result.external_actions_performed is True
    assert store._items[result.publication_id].status == "scheduled"
    assert store._items[result.publication_id].external_id == "ext-1"


def test_external_failure_is_recorded():
    class FailingAdapter:
        def publish(self, payload):
            raise RuntimeError("provider down")

    gate, approval = approved_gate()
    store = InMemoryPublicationStore()
    service = PublisherService(gate, adapter=FailingAdapter(), publication_store=store)
    with pytest.raises(RuntimeError, match="provider down"):
        service.publish(
            run_id="run-1", approval_id=approval.id, payload=PAYLOAD, execution_authorized=True
        )
    assert any(item.status == "failed" and item.error == "provider down" for item in store._items.values())
