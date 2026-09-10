create index if not exists idx_squad_artifacts_task
  on public.squad_artifacts(task_id)
  where task_id is not null;

create index if not exists idx_squad_events_task
  on public.squad_events(task_id)
  where task_id is not null;
