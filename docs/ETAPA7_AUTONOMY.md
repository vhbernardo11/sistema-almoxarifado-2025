# Etapa 7 — Fila, scheduler, retries e recuperação

A Etapa 7 adiciona a camada de autonomia operacional sem retirar as travas humanas de publicação.

## Componentes

- `squad_jobs`: fila persistente com prioridade, idempotência, tentativas, lock e heartbeat.
- `squad_schedules`: agendas recorrentes com intervalo mínimo de 60 segundos.
- `squad_claim_next_job`: claim atômico com `FOR UPDATE SKIP LOCKED` para múltiplos workers.
- `squad_requeue_stale_jobs`: recupera jobs abandonados por worker morto.
- `squad_materialize_due_schedules`: transforma agendas vencidas em jobs idempotentes.
- `Worker`: executa um job por tick, aplica backoff exponencial e nunca esconde loop infinito.
- `CheckpointResumeCoordinator`: converte checkpoint persistido em job `run.resume` idempotente.

## Segurança e limites

O Worker não publica diretamente e não conhece Metricool. A Etapa 4 continua sendo o único caminho para publicação, com ApprovalGate e autorização explícita de execução. As tabelas novas têm RLS e não concedem acesso direto a `anon` ou `authenticated`.

## Backoff

Por padrão: 15s, 30s, 60s... limitado a 900s. Ao esgotar `max_attempts`, o job termina como `failed`. Se houver `run_id` e checkpoint retomável, um recovery job pode ser enfileirado uma única vez via idempotency key.

## Scheduler

O scheduler materializa jobs; ele não executa agentes dentro do banco. Um processo Worker precisa chamar `tick()` periodicamente. Hospedar esse processo continuamente é uma decisão de infraestrutura separada e exige segredos de backend (`SUPABASE_SERVICE_ROLE_KEY` e, para agentes, `OPENAI_API_KEY`).
