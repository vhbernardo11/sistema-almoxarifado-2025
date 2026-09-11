# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapa 1: consolidação persistente no GitHub;
- Etapa 2: núcleo textual estruturado Researcher -> Strategist -> Copywriter;
- Etapa 3: memória/estado persistentes no Supabase com runs, tasks, artifacts, events, checkpoints e memories;
- Etapa 4: ApprovalGate fail-closed e Publisher preparado;
- Etapa 5: contratos de mídia e renderer determinístico via FFmpeg;
- Etapa 6: QA automático de mídia, templates e SHA-256 ligado à aprovação;
- Etapa 7: fila persistente, scheduler, retry/backoff, heartbeat e recuperação por checkpoint;
- Etapa 8: runtime hospedado test-only no Supabase Edge Functions, cron a cada 5 minutos, atores sintéticos, telemetria e alertas internos.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana pertence ao mesmo `run_id` e payload exato;
- alteração de conteúdo ou mídia invalida autorização anterior;
- o Publisher exige autorização explícita além da aprovação;
- jobs externos devem ser idempotentes sempre que possível;
- autonomia operacional não atravessa a barreira de aprovação;
- segredos ficam fora do Git;
- Etapa 8 usa somente usuários de teste `stage8-test-*`.

## O que a Etapa 8 resolve
- existe um runtime hospedado que acorda sozinho por cron;
- o cron usa token aleatório guardado no Supabase Vault;
- o worker hospedado só reclama jobs sintéticos `test.*`;
- telemetria de ticks é persistida em `squad_runtime_ticks`;
- alertas internos ficam em `squad_runtime_alerts`;
- `test.retry_once` foi validado end-to-end: primeira tentativa em retry e segunda concluída automaticamente pelo cron;
- `test.waiting_approval` foi validado com `publication_authorized=false`.

## Limites atuais
- o runtime hospedado é propositalmente test-only;
- handlers Python reais `text_core.run` e `media.review` estão conectados no código, mas ainda não são executados pela Edge Function Deno;
- publicação real continua deliberadamente bloqueada até aprovação + autorização explícita;
- Reviewer de mídia ainda não faz compreensão visual semântica quadro a quadro;
- não existe dashboard operacional completo;
- alertas ainda são internos no banco, sem envio externo automático.

## Próximo passo
Etapa 9 recomendada: dashboard operacional para runs, fila, ticks, falhas, retries, aprovações e alertas; depois disso, promover handlers reais para um runtime backend controlado, mantendo usuários teste como padrão durante a homologação.
