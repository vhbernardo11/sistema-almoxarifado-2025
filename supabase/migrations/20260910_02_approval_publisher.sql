create table if not exists public.squad_approvals (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.squad_runs(id) on delete cascade,
  content_digest text not null,
  decision text not null default 'pending' check (decision in ('pending','approved','changes_requested','rejected')),
  approver text,
  note text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  decided_at timestamptz
);

create index if not exists idx_squad_approvals_run on public.squad_approvals(run_id);
create index if not exists idx_squad_approvals_decision on public.squad_approvals(decision);
alter table public.squad_approvals enable row level security;
revoke all on table public.squad_approvals from anon, authenticated;

create table if not exists public.squad_publications (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.squad_runs(id) on delete cascade,
  approval_id uuid not null references public.squad_approvals(id) on delete restrict,
  provider text not null,
  target jsonb not null,
  status text not null default 'prepared',
  external_id text,
  planner_url text,
  attempted_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_squad_publications_run on public.squad_publications(run_id);
create index if not exists idx_squad_publications_approval on public.squad_publications(approval_id);
alter table public.squad_publications enable row level security;
revoke all on table public.squad_publications from anon, authenticated;
