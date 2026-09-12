create or replace function public.squad_invoke_stage15_test_worker(p_max_jobs integer default 5)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  request_id bigint;
  worker_token text;
begin
  select decrypted_secret into worker_token
  from vault.decrypted_secrets
  where name = 'integrasquad_stage8_worker_token'
  limit 1;

  if worker_token is null then
    raise exception 'stage15 worker token ausente';
  end if;

  select net.http_post(
    url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage15-worker',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'x-integrasquad-worker-token', worker_token
    ),
    body := jsonb_build_object('max_jobs', least(greatest(p_max_jobs,1),10))
  ) into request_id;

  return request_id;
end;
$$;

revoke all on function public.squad_invoke_stage15_test_worker(integer) from public, anon, authenticated;
