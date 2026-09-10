from __future__ import annotations

from datetime import datetime, timezone

import pytest

from integra.approval import ApprovalError, ApprovalGate, InMemoryApprovalStore
from integra.publisher import PublicationReceipt, PublisherError, PublisherService


PAYLOAD = {"network": "instagram", "text": "Conheça o IntegraTrampo", "media": ["https://example.org/post.png"]}


def make_gate():
    return ApprovalGate(InMemoryApprovalStore())


def test_pending_changes_and_rejected_never_authorize_publication():
    for decision in [None, "changes_requested", "rejected"]:
        gate = make_gate()
        approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
        if decision:
            gate.decide(approval.id, decision=decision, approver="humano")
        with pytest.raises(ApprovalError):
            gate.validate_for_publication(approval_id=approval.id, run_id="run-1", payload=PAYLOAD)


def test_approved_exact_payload_passes_but_changed_payload_fails():
    gate = make_gate()
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    assert gate.validate_for_publication(approval_id=approval.id, run_id="run-1", payload=PAYLOAD).decision == "approved"
    changed = dict(PAYLOAD, text="Texto alterado depois da aprovação")
    with pytest.raises(ApprovalError, match="mudou"):
        gate.validate_for_publication(approval_id=approval.id, run_id="run-1", payload=changed)


def test_approval_cannot_be_reused_for_another_run():
    gate = make_gate()
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    with pytest.raises(ApprovalError, match="não pertence"):
        gate.validate_for_publication(approval_id=approval.id, run_id="run-2", payload=PAYLOAD)


def test_prepare_never_calls_external_adapter():
    calls = []

    class FakeAdapter:
        def publish(self, payload):
            calls.append(payload)
            return PublicationReceipt(provider="fake", status="scheduled", executed_at=datetime.now(timezone.utc))

    gate = make_gate()
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    result = PublisherService(gate, FakeAdapter()).prepare(run_id="run-1", approval_id=approval.id, payload=PAYLOAD)
    assert result.ready is True
    assert result.external_actions_performed is False
    assert calls == []


def test_publish_requires_second_explicit_execution_authorization():
    gate = make_gate()
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    service = PublisherService(gate, adapter=None)
    with pytest.raises(PublisherError, match="autorização explícita"):
        service.publish(run_id="run-1", approval_id=approval.id, payload=PAYLOAD)


def test_publish_calls_adapter_only_after_both_gates():
    calls = []

    class FakeAdapter:
        def publish(self, payload):
            calls.append(payload)
            return PublicationReceipt(provider="fake", external_id="123", status="scheduled")

    gate = make_gate()
    approval = gate.request_approval(run_id="run-1", payload=PAYLOAD)
    gate.decide(approval.id, decision="approved", approver="humano")
    result = PublisherService(gate, FakeAdapter()).publish(
        run_id="run-1", approval_id=approval.id, payload=PAYLOAD, execution_authorized=True
    )
    assert calls == [PAYLOAD]
    assert result.publication_attempted is True
    assert result.external_actions_performed is True
