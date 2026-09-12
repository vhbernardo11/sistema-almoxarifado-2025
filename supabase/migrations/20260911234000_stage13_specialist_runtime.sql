create or replace function public.squad_claim_next_stage13_specialist_job(p_worker_id text)
returns setof public.squad_jobs
language plpgsql security definer set search_path = public as $$
begin
  return query
  with candidate as (
    select j.id
    from public.squad_jobs j
    join public.squad_test_actors a on a.id = j.payload->>'test_actor_id' and a.enabled = true
    where j.status in ('pending','retry')
      and j.available_at <= now()
      and j.job_type like 'specialist.%'
      and coalesce((j.payload->>'test_mode')::boolean, false) = true
      and coalesce((j.payload->>'publication_authorized')::boolean, false) = false
      and coalesce((j.payload->>'external_actions_authorized')::boolean, false) = false
    order by j.priority desc, j.available_at, j.created_at
    for update of j skip locked limit 1
  )
  update public.squad_jobs j set status='running',attempt=j.attempt+1,locked_by=p_worker_id,locked_at=now(),heartbeat_at=now(),last_error=null
  from candidate where j.id=candidate.id returning j.*;
end; $$;

create or replace function public.squad_requeue_stale_stage13_specialist_jobs(p_stale_seconds integer default 300)
returns integer language plpgsql security definer set search_path = public as $$
declare affected integer;
begin
  with changed as (
    update public.squad_jobs j set
      status=case when j.attempt<j.max_attempts then 'retry' else 'failed' end,
      available_at=case when j.attempt<j.max_attempts then now() else j.available_at end,
      finished_at=case when j.attempt<j.max_attempts then null else now() end,
      locked_by=null,locked_at=null,heartbeat_at=null,last_error='stage13 heartbeat expirado; job sintético recuperado'
    from public.squad_test_actors a
    where j.status='running' and j.job_type like 'specialist.%'
      and coalesce((j.payload->>'test_mode')::boolean,false)=true
      and a.id=j.payload->>'test_actor_id' and a.enabled=true
      and coalesce(j.heartbeat_at,j.locked_at,j.created_at)<now()-make_interval(secs=>greatest(p_stale_seconds,1))
    returning 1)
  select count(*) into affected from changed; return affected;
end; $$;

create or replace function public.squad_materialize_due_stage13_specialist_schedules(p_limit integer default 25)
returns integer language plpgsql security definer set search_path = public as $$
declare s public.squad_schedules%rowtype; created_count integer:=0; slot_key text;
begin
 for s in select q.* from public.squad_schedules q join public.squad_test_actors a on a.id=q.payload->>'test_actor_id' and a.enabled=true
   where q.enabled=true and q.next_run_at<=now() and q.job_type like 'specialist.%'
     and coalesce((q.payload->>'test_mode')::boolean,false)=true
     and coalesce((q.payload->>'publication_authorized')::boolean,false)=false
     and coalesce((q.payload->>'external_actions_authorized')::boolean,false)=false
   order by q.next_run_at for update of q skip locked limit greatest(p_limit,1)
 loop
   slot_key:='stage13-specialist-schedule:'||s.id::text||':'||extract(epoch from s.next_run_at)::bigint::text;
   insert into public.squad_jobs(job_type,payload,priority,max_attempts,idempotency_key) values(s.job_type,s.payload,s.priority,s.max_attempts,slot_key) on conflict(idempotency_key) do nothing;
   if found then created_count:=created_count+1; end if;
   update public.squad_schedules set next_run_at=now()+make_interval(secs=>interval_seconds) where id=s.id;
 end loop; return created_count;
end; $$;

revoke all on function public.squad_claim_next_stage13_specialist_job(text) from public,anon,authenticated;
revoke all on function public.squad_requeue_stale_stage13_specialist_jobs(integer) from public,anon,authenticated;
revoke all on function public.squad_materialize_due_stage13_specialist_schedules(integer) from public,anon,authenticated;
grant execute on function public.squad_claim_next_stage13_specialist_job(text) to service_role;
grant execute on function public.squad_requeue_stale_stage13_specialist_jobs(integer) to service_role;
grant execute on function public.squad_materialize_due_stage13_specialist_schedules(integer) to service_role;

select cron.schedule(
  'integrasquad-stage13-specialist-worker',
  '*/5 * * * *',
  $$select net.http_post(
      url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage13-worker',
      headers := jsonb_build_object('Content-Type','application/json','x-integrasquad-worker-token',(select decrypted_secret from vault.decrypted_secrets where name='integrasquad_stage8_worker_token' limit 1)),
      body := '{"max_jobs":10}'::jsonb
    );$$
);