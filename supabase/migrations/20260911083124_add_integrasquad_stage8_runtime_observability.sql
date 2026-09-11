create table if not exists public.squad_test_actors (
  id text primary key check (id like 'stage8-test-%'),
  display_name text not null,
  email text not null check (email like '%@example.invalid'),
  enabled boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.squad_runtime_ticks (
  id uuid primary key default gen_random_uuid(),
  worker_id text not null,
  mode text not null default 'test' check (mode = 'test'),
  status text not null default 'running' check (status in ('running','completed','failed')),
  jobs_claimed integer not null default 0,
  jobs_completed integer not null default 0,
  jobs_retried integer not null default 0,
  jobs_failed integer not null default 0,
  schedules_materialized integer not null default 0,
  stale_jobs_requeued integer not null default 0,
  detail jsonb not null default '{}'::jsonb,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);

create table if not exists public.squad_runtime_alerts (
  id uuid primary key default gen_random_uuid(),
  test_actor_id text references public.squad_test_actors(id) on delete set null,
  job_id uuid references public.squad_jobs(id) on delete set null,
  severity text not null check (severity in ('info','warning','error')),
  kind text not null,
  message text not null,
  payload jsonb not null default '{}'::jsonb,
  resolved boolean not null default false,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create index if not exists idx_squad_runtime_ticks_started on public.squad_runtime_ticks(started_at desc);
create index if not exists idx_squad_runtime_alerts_open on public.squad_runtime_alerts(created_at desc) where resolved = false;
create index if not exists idx_squad_runtime_alerts_job on public.squad_runtime_alerts(job_id);

alter table public.squad_test_actors enable row level security;
alter table public.squad_runtime_ticks enable row level security;
alter table public.squad_runtime_alerts enable row level security;
revoke all on public.squad_test_actors from anon, authenticated;
revoke all on public.squad_runtime_ticks from anon, authenticated;
revoke all on public.squad_runtime_alerts from anon, authenticated;

insert into public.squad_test_actors(id, display_name, email, metadata)
values
  ('stage8-test-user-001', 'IntegraSquad Test User 001', 'stage8-user-001@example.invalid', '{"purpose":"stage8-runtime-validation"}'::jsonb),
  ('stage8-test-admin-001', 'IntegraSquad Test Admin 001', 'stage8-admin-001@example.invalid', '{"purpose":"stage8-approval-validation"}'::jsonb)
on conflict (id) do update
set display_name = excluded.display_name,
    email = excluded.email,
    enabled = true,
    metadata = excluded.metadata;

create or replace function public.squad_claim_next_test_job(p_worker_id text)
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
      and j.job_type like 'test.%'
      and coalesce((j.payload->>'test_mode')::boolean, false) = true
    order by j.priority desc, j.available_at, j.created_at
    for update of j skip locked
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

create or replace function public.squad_requeue_stale_test_jobs(p_stale_seconds integer default 300)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  affected integer;
begin
  with changed as (
    update public.squad_jobs j
    set status = case when j.attempt < j.max_attempts then 'retry' else 'failed' end,
        available_at = case when j.attempt < j.max_attempts then now() else j.available_at end,
        finished_at = case when j.attempt < j.max_attempts then null else now() end,
        locked_by = null,
        locked_at = null,
        heartbeat_at = null,
        last_error = 'worker heartbeat expirado; job de teste recuperado automaticamente'
    from public.squad_test_actors a
    where j.status = 'running'
      and j.job_type like 'test.%'
      and coalesce((j.payload->>'test_mode')::boolean, false) = true
      and a.id = j.payload->>'test_actor_id'
      and a.enabled = true
      and coalesce(j.heartbeat_at, j.locked_at, j.created_at) < now() - make_interval(secs => greatest(p_stale_seconds, 1))
    returning 1
  )
  select count(*) into affected from changed;
  return affected;
end;
$$;

create or replace function public.squad_materialize_due_test_schedules(p_limit integer default 25)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  schedule_row public.squad_schedules%rowtype;
  created_count integer := 0;
  slot_key text;
begin
  for schedule_row in
    select s.*
    from public.squad_schedules s
    join public.squad_test_actors a on a.id = s.payload->>'test_actor_id' and a.enabled = true
    where s.enabled = true
      and s.next_run_at <= now()
      and s.job_type like 'test.%'
      and coalesce((s.payload->>'test_mode')::boolean, false) = true
    order by s.next_run_at
    for update of s skip locked
    limit greatest(p_limit, 1)
  loop
    slot_key := 'stage8-test-schedule:' || schedule_row.id::text || ':' || extract(epoch from schedule_row.next_run_at)::bigint::text;
    insert into public.squad_jobs(job_type, payload, priority, max_attempts, idempotency_key)
    values(schedule_row.job_type, schedule_row.payload, schedule_row.priority, schedule_row.max_attempts, slot_key)
    on conflict (idempotency_key) do nothing;
    if found then created_count := created_count + 1; end if;
    update public.squad_schedules
    set next_run_at = now() + make_interval(secs => interval_seconds)
    where id = schedule_row.id;
  end loop;
  return created_count;
end;
$$;

revoke all on function public.squad_claim_next_test_job(text) from public, anon, authenticated;
revoke all on function public.squad_requeue_stale_test_jobs(integer) from public, anon, authenticated;
revoke all on function public.squad_materialize_due_test_schedules(integer) from public, anon, authenticated;
grant execute on function public.squad_claim_next_test_job(text) to service_role;
grant execute on function public.squad_requeue_stale_test_jobs(integer) to service_role;
grant execute on function public.squad_materialize_due_test_schedules(integer) to service_role;
