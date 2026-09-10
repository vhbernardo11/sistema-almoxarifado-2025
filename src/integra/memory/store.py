from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .models import ResumeState


class MemoryStoreError(RuntimeError):
    pass


class MemoryStore(Protocol):
    def create_run(self, *, goal: str, context: dict[str, Any], metadata: dict[str, Any] | None = None) -> str: ...
    def create_task(self, *, run_id: str, sequence: int, agent_id: str, objective: str, input_data: dict[str, Any] | None = None) -> str: ...
    def mark_task_running(self, task_id: str) -> None: ...
    def complete_task(self, task_id: str, *, summary: str, result_data: dict[str, Any]) -> None: ...
    def fail_task(self, task_id: str, *, error: str) -> None: ...
    def append_event(self, *, run_id: str, event_type: str, payload: dict[str, Any] | None = None, task_id: str | None = None) -> None: ...
    def save_checkpoint(self, *, run_id: str, checkpoint_key: str, resume_sequence: int | None, snapshot: dict[str, Any]) -> None: ...
    def complete_run(self, run_id: str, *, current_stage: str, metadata: dict[str, Any] | None = None) -> None: ...
    def fail_run(self, run_id: str, *, error: str) -> None: ...
    def save_memory(self, *, scope: str, key: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> None: ...
    def get_memory(self, *, scope: str, key: str) -> dict[str, Any] | None: ...
    def get_resume_state(self, run_id: str) -> ResumeState: ...


class SupabaseMemoryStore:
    """Persistência do IntegraSquad via Supabase/PostgREST.

    A service-role key é aceita apenas no backend e nunca deve ser enviada ao
    navegador, commitada ou registrada em logs.
    """

    def __init__(self, client: Any):
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabaseMemoryStore":
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise MemoryStoreError(
                "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios no ambiente do backend."
            )
        try:
            from supabase import create_client
        except ImportError as exc:
            raise MemoryStoreError(
                "Instale o extra de armazenamento: pip install -e '.[storage]'"
            ) from exc
        return cls(create_client(url, key))

    @staticmethod
    def _data(response: Any) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if data is None and isinstance(response, dict):
            data = response.get("data")
        return list(data or [])

    def create_run(self, *, goal: str, context: dict[str, Any], metadata: dict[str, Any] | None = None) -> str:
        response = self.client.table("squad_runs").insert(
            {
                "goal": goal,
                "status": "running",
                "current_stage": "researcher",
                "context": context,
                "metadata": metadata or {},
            }
        ).execute()
        data = self._data(response)
        if not data:
            raise MemoryStoreError("Supabase não retornou o run criado.")
        return str(data[0]["id"])

    def create_task(self, *, run_id: str, sequence: int, agent_id: str, objective: str, input_data: dict[str, Any] | None = None) -> str:
        response = self.client.table("squad_tasks").insert(
            {
                "run_id": run_id,
                "sequence": sequence,
                "agent_id": agent_id,
                "objective": objective,
                "status": "pending",
                "input": input_data or {},
            }
        ).execute()
        data = self._data(response)
        if not data:
            raise MemoryStoreError("Supabase não retornou a tarefa criada.")
        return str(data[0]["id"])

    def mark_task_running(self, task_id: str) -> None:
        self.client.table("squad_tasks").update(
            {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", task_id).execute()

    def complete_task(self, task_id: str, *, summary: str, result_data: dict[str, Any]) -> None:
        self.client.table("squad_tasks").update(
            {
                "status": "completed",
                "result_summary": summary,
                "result_data": result_data,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", task_id).execute()

    def fail_task(self, task_id: str, *, error: str) -> None:
        self.client.table("squad_tasks").update(
            {
                "status": "failed",
                "error": error,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", task_id).execute()

    def append_event(self, *, run_id: str, event_type: str, payload: dict[str, Any] | None = None, task_id: str | None = None) -> None:
        self.client.table("squad_events").insert(
            {
                "run_id": run_id,
                "task_id": task_id,
                "event_type": event_type,
                "payload": payload or {},
            }
        ).execute()

    def save_checkpoint(self, *, run_id: str, checkpoint_key: str, resume_sequence: int | None, snapshot: dict[str, Any]) -> None:
        self.client.table("squad_checkpoints").upsert(
            {
                "run_id": run_id,
                "checkpoint_key": checkpoint_key,
                "resume_sequence": resume_sequence,
                "snapshot": snapshot,
            },
            on_conflict="run_id,checkpoint_key",
        ).execute()

    def complete_run(self, run_id: str, *, current_stage: str, metadata: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {
            "status": "completed",
            "current_stage": current_stage,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if metadata is not None:
            payload["metadata"] = metadata
        self.client.table("squad_runs").update(payload).eq("id", run_id).execute()

    def fail_run(self, run_id: str, *, error: str) -> None:
        self.client.table("squad_runs").update(
            {"status": "failed", "error": error}
        ).eq("id", run_id).execute()

    def add_artifact(self, *, run_id: str, type: str, path_or_url: str, task_id: str | None = None, checksum_sha256: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        response = self.client.table("squad_artifacts").insert(
            {
                "run_id": run_id,
                "task_id": task_id,
                "type": type,
                "path_or_url": path_or_url,
                "checksum_sha256": checksum_sha256,
                "metadata": metadata or {},
            }
        ).execute()
        data = self._data(response)
        if not data:
            raise MemoryStoreError("Supabase não retornou o artefato criado.")
        return str(data[0]["id"])

    def save_memory(self, *, scope: str, key: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        self.client.table("squad_memories").upsert(
            {
                "scope": scope,
                "memory_key": key,
                "content": content,
                "metadata": metadata or {},
            },
            on_conflict="scope,memory_key",
        ).execute()

    def get_memory(self, *, scope: str, key: str) -> dict[str, Any] | None:
        response = (
            self.client.table("squad_memories")
            .select("content")
            .eq("scope", scope)
            .eq("memory_key", key)
            .limit(1)
            .execute()
        )
        data = self._data(response)
        return deepcopy(data[0]["content"]) if data else None

    def get_resume_state(self, run_id: str) -> ResumeState:
        runs = self._data(
            self.client.table("squad_runs")
            .select("id,status,current_stage")
            .eq("id", run_id)
            .limit(1)
            .execute()
        )
        if not runs:
            raise MemoryStoreError(f"Run não encontrado: {run_id}")

        tasks = self._data(
            self.client.table("squad_tasks")
            .select("sequence,status")
            .eq("run_id", run_id)
            .order("sequence")
            .execute()
        )
        checkpoints = self._data(
            self.client.table("squad_checkpoints")
            .select("checkpoint_key,resume_sequence,snapshot,updated_at")
            .eq("run_id", run_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        checkpoint = checkpoints[0] if checkpoints else {}
        completed = [int(task["sequence"]) for task in tasks if task["status"] == "completed"]
        unfinished = [int(task["sequence"]) for task in tasks if task["status"] != "completed"]

        return ResumeState(
            run_id=run_id,
            run_status=str(runs[0]["status"]),
            current_stage=runs[0].get("current_stage"),
            checkpoint_key=checkpoint.get("checkpoint_key"),
            resume_sequence=checkpoint.get("resume_sequence"),
            snapshot=checkpoint.get("snapshot") or {},
            completed_sequences=completed,
            unfinished_sequences=unfinished,
        )


class InMemoryMemoryStore:
    """Implementação determinística para testes sem rede nem segredos."""

    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        self.checkpoints: dict[tuple[str, str], dict[str, Any]] = {}
        self.memories: dict[tuple[str, str], dict[str, Any]] = {}
        self.artifacts: dict[str, dict[str, Any]] = {}

    def create_run(self, *, goal: str, context: dict[str, Any], metadata: dict[str, Any] | None = None) -> str:
        run_id = str(uuid4())
        self.runs[run_id] = {
            "id": run_id,
            "goal": goal,
            "status": "running",
            "current_stage": "researcher",
            "context": deepcopy(context),
            "metadata": deepcopy(metadata or {}),
            "error": None,
        }
        return run_id

    def create_task(self, *, run_id: str, sequence: int, agent_id: str, objective: str, input_data: dict[str, Any] | None = None) -> str:
        task_id = str(uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "run_id": run_id,
            "sequence": sequence,
            "agent_id": agent_id,
            "objective": objective,
            "status": "pending",
            "input": deepcopy(input_data or {}),
            "result_data": {},
            "error": None,
        }
        return task_id

    def mark_task_running(self, task_id: str) -> None:
        self.tasks[task_id]["status"] = "running"

    def complete_task(self, task_id: str, *, summary: str, result_data: dict[str, Any]) -> None:
        self.tasks[task_id].update(
            status="completed", result_summary=summary, result_data=deepcopy(result_data)
        )

    def fail_task(self, task_id: str, *, error: str) -> None:
        self.tasks[task_id].update(status="failed", error=error)

    def append_event(self, *, run_id: str, event_type: str, payload: dict[str, Any] | None = None, task_id: str | None = None) -> None:
        self.events.append(
            {
                "run_id": run_id,
                "task_id": task_id,
                "event_type": event_type,
                "payload": deepcopy(payload or {}),
            }
        )

    def save_checkpoint(self, *, run_id: str, checkpoint_key: str, resume_sequence: int | None, snapshot: dict[str, Any]) -> None:
        self.checkpoints[(run_id, checkpoint_key)] = {
            "checkpoint_key": checkpoint_key,
            "resume_sequence": resume_sequence,
            "snapshot": deepcopy(snapshot),
            "ordinal": len(self.checkpoints),
        }

    def complete_run(self, run_id: str, *, current_stage: str, metadata: dict[str, Any] | None = None) -> None:
        self.runs[run_id].update(
            status="completed",
            current_stage=current_stage,
            metadata=deepcopy(metadata or self.runs[run_id]["metadata"]),
        )

    def fail_run(self, run_id: str, *, error: str) -> None:
        self.runs[run_id].update(status="failed", error=error)

    def add_artifact(self, *, run_id: str, type: str, path_or_url: str, task_id: str | None = None, checksum_sha256: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        artifact_id = str(uuid4())
        self.artifacts[artifact_id] = {
            "id": artifact_id,
            "run_id": run_id,
            "task_id": task_id,
            "type": type,
            "path_or_url": path_or_url,
            "checksum_sha256": checksum_sha256,
            "metadata": deepcopy(metadata or {}),
        }
        return artifact_id

    def save_memory(self, *, scope: str, key: str, content: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        self.memories[(scope, key)] = {
            "content": deepcopy(content),
            "metadata": deepcopy(metadata or {}),
        }

    def get_memory(self, *, scope: str, key: str) -> dict[str, Any] | None:
        item = self.memories.get((scope, key))
        return deepcopy(item["content"]) if item else None

    def get_resume_state(self, run_id: str) -> ResumeState:
        run = self.runs.get(run_id)
        if not run:
            raise MemoryStoreError(f"Run não encontrado: {run_id}")
        tasks = sorted(
            (task for task in self.tasks.values() if task["run_id"] == run_id),
            key=lambda task: task["sequence"],
        )
        checkpoints = [
            checkpoint
            for (checkpoint_run_id, _), checkpoint in self.checkpoints.items()
            if checkpoint_run_id == run_id
        ]
        checkpoint = max(checkpoints, key=lambda item: item["ordinal"]) if checkpoints else {}
        return ResumeState(
            run_id=run_id,
            run_status=run["status"],
            current_stage=run.get("current_stage"),
            checkpoint_key=checkpoint.get("checkpoint_key"),
            resume_sequence=checkpoint.get("resume_sequence"),
            snapshot=deepcopy(checkpoint.get("snapshot") or {}),
            completed_sequences=[task["sequence"] for task in tasks if task["status"] == "completed"],
            unfinished_sequences=[task["sequence"] for task in tasks if task["status"] != "completed"],
        )
