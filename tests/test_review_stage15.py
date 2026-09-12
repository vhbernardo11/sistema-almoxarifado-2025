import pytest

from integra.review import ReviewCenter, ReviewError, canonical_review_digest


def payload():
    return {
        "route": "software",
        "status": "needs_review",
        "steps": [{"specialist_id": "tester", "status": "completed"}],
        "publication_authorized": False,
        "external_actions_authorized": False,
    }


def test_review_digest_is_canonical():
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert canonical_review_digest(a) == canonical_review_digest(b)


def test_only_test_actor_can_enter_review_queue():
    center = ReviewCenter()
    with pytest.raises(ReviewError, match="stage8-test"):
        center.create(job_id="job-1", actor_id="usuario-real", route="software", payload=payload())


def test_review_is_idempotent_per_job_and_bound_to_payload():
    center = ReviewCenter()
    first = center.create(job_id="job-1", actor_id="stage8-test-user-001", route="software", payload=payload())
    second = center.create(job_id="job-1", actor_id="stage8-test-user-001", route="software", payload=payload())
    assert first.id == second.id
    changed = payload()
    changed["status"] = "completed"
    with pytest.raises(ReviewError, match="trocar de conteúdo"):
        center.create(job_id="job-1", actor_id="stage8-test-user-001", route="software", payload=changed)


def test_acceptance_never_authorizes_publication_or_external_effects():
    center = ReviewCenter()
    item = center.create(job_id="job-1", actor_id="stage8-test-user-001", route="software", payload=payload())
    decided = center.decide(item.id, decision="accepted", reviewer="stage8-test-admin-001", note="homologação sintética")
    assert decided.decision == "accepted"
    assert decided.publication_authorized is False
    assert decided.external_actions_authorized is False


def test_decision_requires_test_admin_and_is_immutable():
    center = ReviewCenter()
    item = center.create(job_id="job-1", actor_id="stage8-test-user-001", route="campaign", payload=payload())
    with pytest.raises(ReviewError, match="stage8-test-admin"):
        center.decide(item.id, decision="rejected", reviewer="admin-real")
    center.decide(item.id, decision="changes_requested", reviewer="stage8-test-admin-001")
    with pytest.raises(ReviewError, match="já decidida"):
        center.decide(item.id, decision="accepted", reviewer="stage8-test-admin-001")


def test_modified_payload_is_rejected_after_review_creation():
    center = ReviewCenter()
    item = center.create(job_id="job-1", actor_id="stage8-test-user-001", route="software", payload=payload())
    changed = payload()
    changed["steps"].append({"specialist_id": "reviewer", "status": "completed"})
    with pytest.raises(ReviewError, match="conteúdo mudou"):
        center.validate_payload(item.id, changed)
