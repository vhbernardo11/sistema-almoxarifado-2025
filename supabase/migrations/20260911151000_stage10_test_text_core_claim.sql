create or replace function public.squad_claim_next_stage10_test_job(p_worker_id text)
returns setof public.squad_jobs
language plpgsql
security definer
set search_path = public
as $function$
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
      and j.job_type = 'text_core.run'
      and coalesce((j.payload->>'test_mode')::boolean, false) = true
      and j.payload->>'test_actor_id' like 'stage8-test-%'
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
$function$;

revoke all on function public.squad_claim_next_stage10_test_job(text) from public, anon, authenticated;
grant execute on function public.squad_claim_next_stage10_test_job(text) to service_role;
