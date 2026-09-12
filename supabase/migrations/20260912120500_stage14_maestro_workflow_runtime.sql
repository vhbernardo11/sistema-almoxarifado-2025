create or replace function public.squad_claim_next_stage14_workflow_job(p_worker_id text)
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
    join public.squad_test_actors a
      on a.id = j.payload->>'test_actor_id'
     and a.enabled = true
    where j.status in ('pending','retry')
      and j.available_at <= now()
      and j.job_type = 'maestro.workflow'
      and coalesce((j.payload->>'test_mode')::boolean, false) = true
      and coalesce((j.payload->>'publication_authorized')::boolean, false) = false
      and coalesce((j.payload->>'external_actions_authorized')::boolean, false) = false
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

create or replace function public.squad_requeue_stale_stage14_workflow_jobs(p_stale_seconds integer default 300)
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
        last_error = 'stage14 worker heartbeat expirado; workflow sintético recuperado automaticamente'
    from public.squad_test_actors a
    where j.status = 'running'
      and j.job_type = 'maestro.workflow'
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

revoke all on function public.squad_claim_next_stage14_workflow_job(text) from public, anon, authenticated;
revoke all on function public.squad_requeue_stale_stage14_workflow_jobs(integer) from public, anon, authenticated;
grant execute on function public.squad_claim_next_stage14_workflow_job(text) to service_role;
grant execute on function public.squad_requeue_stale_stage14_workflow_jobs(integer) to service_role;

do $$
declare
  existing_job bigint;
begin
  select jobid into existing_job from cron.job where jobname = 'integrasquad-stage14-maestro-worker' limit 1;
  if existing_job is not null then
    perform cron.unschedule(existing_job);
  end if;
end $$;

select cron.schedule(
  'integrasquad-stage14-maestro-worker',
  '*/5 * * * *',
  $$
  select net.http_post(
    url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage14-worker',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-integrasquad-worker-token', (
        select decrypted_secret
        from vault.decrypted_secrets
        where name = 'integrasquad_stage8_worker_token'
        limit 1
      )
    ),
    body := '{"max_jobs":3}'::jsonb
  );
  $$
);
