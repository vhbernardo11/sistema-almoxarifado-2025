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

## Fluxo atual

`CampaignRequest -> agentes -> memória/checkpoints -> mídia -> QA -> aprovação humana -> Publisher preparado`

A Etapa 7 adiciona a camada operacional por baixo do fluxo: `squad_jobs` recebe trabalho idempotente, workers fazem claim atômico, falhas temporárias entram em retry com backoff e jobs abandonados podem ser recuperados por heartbeat expirado. `squad_schedules` materializa trabalhos recorrentes sem misturar agenda com lógica de agente.

A aprovação humana continua **fail-closed**. Autonomia de execução não significa autonomia de publicação: o Publisher segue exigindo aprovação do payload exato e autorização explícita de execução.

## Persistência

O projeto usa tabelas `squad_*` isoladas no Supabase para runs, tasks, artifacts, events, checkpoints, memories, approvals, publications, jobs e schedules. As tabelas do IntegraSquad têm RLS habilitado e não concedem acesso direto a `anon` ou `authenticated`; o acesso previsto é server-side.

## Autonomia

O pacote `src/integra/autonomy` contém:
- fila em memória para testes e fila Supabase para produção;
- claim atômico para múltiplos workers;
- prioridade, idempotência, tentativas e backoff exponencial;
- heartbeat e recuperação de worker interrompido;
- scheduler recorrente com intervalo mínimo de 60 segundos;
- `CheckpointResumeCoordinator` para transformar um checkpoint retomável em job `run.resume`.

O Worker executa um `tick()` por chamada ou drena apenas até um limite explícito. Não existe loop infinito escondido no SDK. Para operar 24/7 ainda é necessário hospedar/invocar o Worker em um runtime backend com os segredos apropriados.

## Mídia e aprovação

O QA de mídia verifica SHA-256, resolução, proporção, FPS, duração, codec e áudio quando exigido. O SHA-256 da mídia faz parte do payload de aprovação. Qualquer alteração do vídeo, texto, conta, horário ou destino invalida a autorização anterior.

## Princípios

- agentes pensam e produzem; ferramentas executam ações externas;
- nenhuma publicação externa sem aprovação humana explícita;
- autonomia operacional não contorna ApprovalGate nem Publisher;
- segredos nunca entram no Git;
- cada etapa precisa ser testável isoladamente;
- tarefas precisam ser idempotentes e retomáveis sempre que possível.

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
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/REBUILD_ROADMAP.md`
