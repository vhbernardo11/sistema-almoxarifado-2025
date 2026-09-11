select vault.create_secret(gen_random_uuid()::text, 'integrasquad_stage8_worker_token', 'Token interno do cron para o worker test-only da Etapa 8')
where not exists (select 1 from vault.secrets where name = 'integrasquad_stage8_worker_token');

create or replace function public.squad_verify_stage8_worker_token(p_token text)
returns boolean
language sql
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from vault.decrypted_secrets
    where name = 'integrasquad_stage8_worker_token'
      and decrypted_secret = p_token
  );
$$;

revoke all on function public.squad_verify_stage8_worker_token(text) from public, anon, authenticated;
grant execute on function public.squad_verify_stage8_worker_token(text) to service_role;

select cron.unschedule(jobid)
from cron.job
where jobname = 'integrasquad-stage8-test-worker';

select cron.schedule(
  'integrasquad-stage8-test-worker',
  '*/5 * * * *',
  $cron$
  select net.http_post(
    url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage8-worker',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-integrasquad-worker-token', (
        select decrypted_secret
        from vault.decrypted_secrets
        where name = 'integrasquad_stage8_worker_token'
        limit 1
      )
    ),
    body := '{"max_jobs":5}'::jsonb
  );
  $cron$
);
