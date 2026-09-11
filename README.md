# IntegraSquad

Repositório canônico do **IntegraSquad**, o motor multiagente da Integra.

## Estado atual

- ✅ Etapa 1 — consolidação no GitHub
- ✅ Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter
- ✅ Etapa 3 — memória e estado persistentes no Supabase
- ✅ Etapa 4 — aprovação humana + Publisher preparado
- ✅ Etapa 5 — núcleo de mídia determinístico, sem depender de TTS
- ✅ Etapa 6 — Reviewer de mídia, templates e ponte de aprovação/publicação
- ✅ Etapa 7 — fila persistente, scheduler, retries, heartbeat e recuperação por checkpoint
- ✅ Etapa 8 — runtime hospedado test-only, cron, observabilidade e alertas internos

## Fluxo atual

`CampaignRequest -> agentes -> memória/checkpoints -> mídia -> QA -> aprovação humana -> Publisher preparado`

Por baixo desse fluxo existe agora uma camada operacional persistente: `squad_jobs`, `squad_schedules`, workers, retries, heartbeat, recovery e um runtime hospedado no Supabase.

## Etapa 8: runtime seguro de teste

A Edge Function `integrasquad-stage8-worker` é invocada automaticamente a cada 5 minutos pelo `pg_cron`. Nesta fase ela é deliberadamente **test-only**:

- só aceita jobs `test.*`;
- exige `test_mode=true`;
- exige ator cadastrado com ID `stage8-test-*`;
- usa apenas identidades sintéticas com e-mail `@example.invalid`;
- não registra `publisher.execute`;
- não publica, não agenda post e não contata usuários reais.

O token interno do worker é criado no Supabase Vault e nunca é gravado no Git.

## Observabilidade

- `squad_runtime_ticks`: telemetria de cada execução do runtime;
- `squad_runtime_alerts`: falhas e estados que exigem atenção;
- `squad_test_actors`: usuários sintéticos autorizados para testes.

O teste end-to-end da Etapa 8 comprovou execução normal, retry automático até sucesso e espera por aprovação com `publication_authorized=false`.

## Runtime Python

O pacote `src/integra/runtime` conecta os handlers reais:

- `text_core.run`;
- `media.review`;
- handlers sintéticos de teste.

Todos permanecem atrás do guard de usuário de teste. O Publisher continua ausente do registro automático e falha fechado se alguém tentar enfileirá-lo.

## Segurança

A aprovação humana continua **fail-closed**. Autonomia de execução não significa autonomia de publicação: o Publisher exige aprovação do payload exato e uma autorização explícita de execução.

As tabelas `squad_*` usam RLS e não concedem acesso direto a `anon` ou `authenticated`; operações internas usam backend/service role.

## Testes

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

## Documentação

- `docs/ETAPA2_TEXT_CORE.md`
- `docs/ETAPA3_MEMORY.md`
- `docs/ETAPA4_APPROVAL_PUBLISHER.md`
- `docs/ETAPA5_MEDIA.md`
- `docs/ETAPA6_REVIEW.md`
- `docs/ETAPA7_AUTONOMY.md`
- `docs/ETAPA8_RUNTIME.md`
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/REBUILD_ROADMAP.md`
