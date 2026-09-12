create table if not exists public.squad_workflow_reviews (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.squad_jobs(id) on delete cascade,
  test_actor_id text not null check (test_actor_id like 'stage8-test-%'),
  route text not null,
  payload_digest text not null check (length(payload_digest) = 64),
  review_payload jsonb not null default '{}'::jsonb,
  decision text not null default 'pending' check (decision in ('pending','accepted','changes_requested','rejected')),
  reviewer text,
  note text,
  metadata jsonb not null default '{}'::jsonb,
  publication_authorized boolean not null default false check (publication_authorized = false),
  external_actions_authorized boolean not null default false check (external_actions_authorized = false),
  created_at timestamptz not null default now(),
  decided_at timestamptz,
  check (
    (decision = 'pending' and reviewer is null and decided_at is null)
    or
    (decision <> 'pending' and reviewer is not null and decided_at is not null)
  )
);

create index if not exists idx_squad_workflow_reviews_decision_created
  on public.squad_workflow_reviews(decision, created_at desc);
create index if not exists idx_squad_workflow_reviews_actor
  on public.squad_workflow_reviews(test_actor_id, created_at desc);

alter table public.squad_workflow_reviews enable row level security;
revoke all on table public.squad_workflow_reviews from anon, authenticated;

create or replace function public.squad_decide_stage15_review(
  p_review_id uuid,
  p_decision text,
  p_reviewer text,
  p_note text default null
)
returns public.squad_workflow_reviews
language plpgsql
security definer
set search_path = ''
as $$
declare
  item public.squad_workflow_reviews;
begin
  if p_decision not in ('accepted','changes_requested','rejected') then
    raise exception 'decisão de revisão inválida';
  end if;
  if p_reviewer is null or p_reviewer not like 'stage8-test-admin-%' then
    raise exception 'reviewer deve ser ator sintético stage8-test-admin-*';
  end if;

  select * into item
  from public.squad_workflow_reviews
  where id = p_review_id
  for update;

  if item.id is null then
    raise exception 'revisão não encontrada';
  end if;
  if item.test_actor_id not like 'stage8-test-%' then
    raise exception 'revisão fora do boundary test-only';
  end if;
  if item.decision <> 'pending' then
    raise exception 'revisão já decidida';
  end if;

  update public.squad_workflow_reviews
  set decision = p_decision,
      reviewer = p_reviewer,
      note = p_note,
      decided_at = now(),
      publication_authorized = false,
      external_actions_authorized = false
  where id = p_review_id
  returning * into item;

  return item;
end;
$$;

revoke all on function public.squad_decide_stage15_review(uuid,text,text,text) from public, anon, authenticated;
grant execute on function public.squad_decide_stage15_review(uuid,text,text,text) to service_role;

create or replace function public.squad_invoke_stage15_review_worker(p_max_reviews integer default 10)
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
    raise exception 'worker token ausente';
  end if;

  select net.http_post(
    url := 'https://ghspaqawzfqtsxibgqxy.supabase.co/functions/v1/integrasquad-stage15-review-worker',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'x-integrasquad-worker-token', worker_token
    ),
    body := jsonb_build_object('max_reviews', least(greatest(p_max_reviews,1),25))
  ) into request_id;

  return request_id;
end;
$$;

revoke all on function public.squad_invoke_stage15_review_worker(integer) from public, anon, authenticated;
grant execute on function public.squad_invoke_stage15_review_worker(integer) to service_role;

do $$
declare
  existing bigint;
begin
  select jobid into existing from cron.job where jobname = 'integrasquad-stage15-review-worker' limit 1;
  if existing is not null then
    perform cron.unschedule(existing);
  end if;
  perform cron.schedule(
    'integrasquad-stage15-review-worker',
    '2-59/5 * * * *',
    $cron$select public.squad_invoke_stage15_review_worker(10);$cron$
  );
end;
$$;
