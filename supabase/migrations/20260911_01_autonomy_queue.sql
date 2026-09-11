create table if not exists public.squad_jobs (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.squad_runs(id) on delete cascade,
  task_id uuid references public.squad_tasks(id) on delete set null,
  job_type text not null,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'pending' check (status in ('pending','running','retry','completed','failed','cancelled')),
  priority integer not null default 100,
  attempt integer not null default 0 check (attempt >= 0),
  max_attempts integer not null default 3 check (max_attempts > 0),
  available_at timestamptz not null default now(),
  locked_by text,
  locked_at timestamptz,
  heartbeat_at timestamptz,
  last_error text,
  result jsonb not null default '{}'::jsonb,
  idempotency_key text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  finished_at timestamptz
);

create table if not exists public.squad_schedules (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  job_type text not null,
  payload jsonb not null default '{}'::jsonb,
  interval_seconds integer not null check (interval_seconds >= 60),
  next_run_at timestamptz not null,
  enabled boolean not null default true,
  priority integer not null default 100,
  max_attempts integer not null default 3 check (max_attempts > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_squad_jobs_due
  on public.squad_jobs(status, priority desc, available_at, created_at)
  where status in ('pending','retry');
create index if not exists idx_squad_jobs_run on public.squad_jobs(run_id);
create index if not exists idx_squad_jobs_heartbeat on public.squad_jobs(heartbeat_at)
  where status = 'running';
create index if not exists idx_squad_schedules_due on public.squad_schedules(next_run_at)
  where enabled = true;

alter table public.squad_jobs enable row level security;
alter table public.squad_schedules enable row level security;
revoke all on public.squad_jobs from anon, authenticated;
revoke all on public.squad_schedules from anon, authenticated;

drop trigger if exists trg_squad_jobs_touch on public.squad_jobs;
create trigger trg_squad_jobs_touch before update on public.squad_jobs
for each row execute function public.squad_touch_updated_at();

drop trigger if exists trg_squad_schedules_touch on public.squad_schedules;
create trigger trg_squad_schedules_touch before update on public.squad_schedules
for each row execute function public.squad_touch_updated_at();

create or replace function public.squad_claim_next_job(p_worker_id text)
returns setof public.squad_jobs
language plpgsql
set search_path = public
as $$
begin
  return query
  with candidate as (
    select id
    from public.squad_jobs
    where status in ('pending','retry')
      and available_at <= now()
    order by priority desc, available_at, created_at
    for update skip locked
    limit 1
  )
  update public.squad_jobs as j
  set status = 'running',
      attempt = j.attempt + 1,
      locked_by = p_worker_id,
      locked_at = now(),
      heartbeat_at = now(),
      last_error = null
  from candidate
  where j.id = candidate.id
  returning j.*;
end;
$$;

create or replace function public.squad_requeue_stale_jobs(p_stale_seconds integer default 300)
returns integer
language plpgsql
set search_path = public
as $$
declare
  affected integer;
begin
  with changed as (
    update public.squad_jobs
    set status = case when attempt < max_attempts then 'retry' else 'failed' end,
        available_at = case when attempt < max_attempts then now() else available_at end,
        finished_at = case when attempt < max_attempts then null else now() end,
        locked_by = null,
        locked_at = null,
        heartbeat_at = null,
        last_error = 'worker heartbeat expirado; job recuperado automaticamente'
    where status = 'running'
      and coalesce(heartbeat_at, locked_at, created_at) < now() - make_interval(secs => greatest(p_stale_seconds, 1))
    returning 1
  )
  select count(*) into affected from changed;
  return affected;
end;
$$;

create or replace function public.squad_materialize_due_schedules(p_limit integer default 25)
returns integer
language plpgsql
set search_path = public
as $$
declare
  schedule_row public.squad_schedules%rowtype;
  created_count integer := 0;
  slot_key text;
begin
  for schedule_row in
    select *
    from public.squad_schedules
    where enabled = true and next_run_at <= now()
    order by next_run_at
    for update skip locked
    limit greatest(p_limit, 1)
  loop
    slot_key := 'schedule:' || schedule_row.id::text || ':' || extract(epoch from schedule_row.next_run_at)::bigint::text;
    insert into public.squad_jobs(job_type, payload, priority, max_attempts, idempotency_key)
    values(schedule_row.job_type, schedule_row.payload, schedule_row.priority, schedule_row.max_attempts, slot_key)
    on conflict (idempotency_key) do nothing;
    if found then
      created_count := created_count + 1;
    end if;
    update public.squad_schedules
    set next_run_at = now() + make_interval(secs => interval_seconds)
    where id = schedule_row.id;
  end loop;
  return created_count;
end;
$$;

revoke all on function public.squad_claim_next_job(text) from public, anon, authenticated;
revoke all on function public.squad_requeue_stale_jobs(integer) from public, anon, authenticated;
revoke all on function public.squad_materialize_due_schedules(integer) from public, anon, authenticated;
grant execute on function public.squad_claim_next_job(text) to service_role;
grant execute on function public.squad_requeue_stale_jobs(integer) to service_role;
grant execute on function public.squad_materialize_due_schedules(integer) to service_role;

comment on table public.squad_jobs is 'Fila persistente, idempotente e recuperável do IntegraSquad.';
comment on table public.squad_schedules is 'Agendamentos recorrentes que materializam jobs na fila.';
