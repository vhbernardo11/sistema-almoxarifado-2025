create table if not exists public.squad_workflows (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.squad_jobs(id) on delete cascade,
  actor_id text not null,
  route text not null,
  objective text not null,
  status text not null default 'running' check (status in ('running','retry','blocked','completed','needs_review','failed')),
  current_step integer not null default 0 check (current_step >= 0),
  step_count integer not null check (step_count >= 0),
  completed_steps integer not null default 0 check (completed_steps >= 0),
  requires_human_review boolean not null default false,
  publication_authorized boolean not null default false check (publication_authorized = false),
  external_actions_authorized boolean not null default false check (external_actions_authorized = false),
  state jsonb not null default '{}'::jsonb,
  last_error text,
  started_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.squad_workflow_steps (
  id uuid primary key default gen_random_uuid(),
  workflow_id uuid not null references public.squad_workflows(id) on delete cascade,
  sequence integer not null check (sequence >= 0),
  specialist_id text not null,
  status text not null default 'pending' check (status in ('pending','running','completed','needs_review','failed')),
  attempt integer not null default 0 check (attempt >= 0),
  input jsonb not null default '{}'::jsonb,
  result jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(workflow_id, sequence)
);

create index if not exists idx_squad_workflows_actor_status on public.squad_workflows(actor_id,status);
create index if not exists idx_squad_workflows_updated on public.squad_workflows(updated_at desc);
create index if not exists idx_squad_workflow_steps_workflow on public.squad_workflow_steps(workflow_id,sequence);

alter table public.squad_workflows enable row level security;
alter table public.squad_workflow_steps enable row level security;
revoke all on public.squad_workflows from anon, authenticated;
revoke all on public.squad_workflow_steps from anon, authenticated;

create or replace function public.squad_claim_next_stage15_workflow_job(p_worker_id text)
returns setof public.squad_jobs
language plpgsql
security definer
set search_path = public
as $$
begin
  return query
  with candidate as (
    select j.id
    from public.squad_jobs j
    join public.squad_test_actors a on a.id = j.payload->>'test_actor_id' and a.enabled = true
    where j.status in ('pending','retry')
      and j.available_at <= now()
      and j.job_type = 'maestro.workflow.v2'
      and coalesce((j.payload->>'test_mode')::boolean,false) = true
      and coalesce((j.payload->>'publication_authorized')::boolean,false) = false
      and coalesce((j.payload->>'external_actions_authorized')::boolean,false) = false
    order by j.priority desc, j.available_at, j.created_at
    for update of j skip locked
    limit 1
  )
  update public.squad_jobs j
  set status='running', locked_by=p_worker_id, locked_at=now(), heartbeat_at=now(), last_error=null
  from candidate where j.id=candidate.id
  returning j.*;
end;
$$;

create or replace function public.squad_requeue_stale_stage15_workflow_jobs(p_stale_seconds integer default 300)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare affected integer;
begin
  with changed as (
    update public.squad_jobs j
    set attempt=j.attempt+1,
        status=case when j.attempt+1 < j.max_attempts then 'retry' else 'failed' end,
        available_at=case when j.attempt+1 < j.max_attempts then now() else j.available_at end,
        finished_at=case when j.attempt+1 < j.max_attempts then null else now() end,
        locked_by=null, locked_at=null, heartbeat_at=null,
        last_error='stage15 worker heartbeat expirado; retomada durável agendada'
    from public.squad_test_actors a
    where j.status='running' and j.job_type='maestro.workflow.v2'
      and a.id=j.payload->>'test_actor_id' and a.enabled=true
      and coalesce(j.heartbeat_at,j.locked_at,j.created_at) < now() - make_interval(secs=>greatest(p_stale_seconds,1))
    returning 1
  ) select count(*) into affected from changed;
  return affected;
end;
$$;

select cron.unschedule(jobid) from cron.job where jobname='integrasquad-stage15-durable-worker';
select cron.schedule(
  'integrasquad-stage15-durable-worker',
  '*/5 * * * *',
  $$select net.http_post(
    url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage15-worker',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'x-integrasquad-worker-token',(select decrypted_secret from vault.decrypted_secrets where name='integrasquad_stage8_worker_token' limit 1)
    ),
    body := '{"max_jobs":3}'::jsonb
  );$$
);
