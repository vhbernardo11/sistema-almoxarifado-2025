from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from integra.memory.models import ResumeState
from integra.memory.store import MemoryStore

from .models import CampaignRequest, TextCoreResult
from .workflow import RunnerFn, TextCoreObserver, run_text_core


STAGES = [
    ("researcher", "Pesquisar fatos, contexto, riscos e fontes."),
    ("strategist", "Transformar a pesquisa em estratégia de comunicação."),
    ("copywriter", "Produzir o pacote textual final sem autorizar publicação."),
]


def _jsonable(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {"value": str(value)}


class _PersistentObserver(TextCoreObserver):
    def __init__(self, *, store: MemoryStore, run_id: str, task_ids: dict[str, str]):
        self.store = store
        self.run_id = run_id
        self.task_ids = task_ids
        self.sequence = {name: index for index, (name, _) in enumerate(STAGES)}

    def stage_started(self, stage: str, prompt: str) -> None:
        task_id = self.task_ids[stage]
        self.store.mark_task_running(task_id)
        self.store.append_event(
            run_id=self.run_id,
            task_id=task_id,
            event_type="task.started",
            payload={"stage": stage},
        )

    def stage_completed(self, stage: str, output: Any) -> None:
        task_id = self.task_ids[stage]
        sequence = self.sequence[stage]
        data = _jsonable(output)
        self.store.complete_task(
            task_id,
            summary=f"{stage} concluído",
            result_data=data,
        )
        self.store.append_event(
            run_id=self.run_id,
            task_id=task_id,
            event_type="task.completed",
            payload={"stage": stage},
        )
        self.store.save_checkpoint(
            run_id=self.run_id,
            checkpoint_key=f"after_{stage}",
            resume_sequence=(sequence + 1 if sequence + 1 < len(STAGES) else None),
            snapshot={"stage": stage, "output": data},
        )

    def stage_failed(self, stage: str, error: Exception) -> None:
        task_id = self.task_ids[stage]
        self.store.fail_task(task_id, error=str(error))
        self.store.append_event(
            run_id=self.run_id,
            task_id=task_id,
            event_type="task.failed",
            payload={"stage": stage, "error": str(error)},
        )


class PersistentTextCoreResult(BaseModel):
    run_id: str
    result: TextCoreResult
    resume_state: ResumeState


def run_text_core_persistent(
    request: CampaignRequest,
    *,
    store: MemoryStore,
    runner: RunnerFn | None = None,
) -> PersistentTextCoreResult:
    """Executa o núcleo textual enquanto registra estado, eventos e checkpoints."""

    request_payload = request.model_dump(mode="json")
    run_id = store.create_run(
        goal=request.goal,
        context={"request": request_payload},
        metadata={"pipeline": "text_core_v1"},
    )
    store.append_event(
        run_id=run_id,
        event_type="run.created",
        payload={"publication_authorized": False},
    )

    task_ids: dict[str, str] = {}
    for sequence, (agent_id, objective) in enumerate(STAGES):
        task_ids[agent_id] = store.create_task(
            run_id=run_id,
            sequence=sequence,
            agent_id=agent_id,
            objective=objective,
            input_data={"request": request_payload},
        )

    observer = _PersistentObserver(store=store, run_id=run_id, task_ids=task_ids)
    try:
        result = run_text_core(request, runner=runner, observer=observer)
    except Exception as exc:
        store.fail_run(run_id, error=str(exc))
        store.append_event(
            run_id=run_id,
            event_type="run.failed",
            payload={"error": str(exc)},
        )
        raise

    store.save_checkpoint(
        run_id=run_id,
        checkpoint_key="text_core_complete",
        resume_sequence=None,
        snapshot={
            "result": result.model_dump(mode="json"),
            "next_stage": "human_approval",
        },
    )
    store.complete_run(
        run_id,
        current_stage="human_approval",
        metadata={"pipeline": "text_core_v1", "publication_authorized": False},
    )
    store.append_event(
        run_id=run_id,
        event_type="run.completed",
        payload={"next_stage": "human_approval", "publication_authorized": False},
    )

    return PersistentTextCoreResult(
        run_id=run_id,
        result=result,
        resume_state=store.get_resume_state(run_id),
    )
