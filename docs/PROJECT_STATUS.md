# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapa 1: consolidação persistente no GitHub;
- Etapa 2: núcleo textual estruturado Researcher -> Strategist -> Copywriter;
- Etapa 3: memória/estado persistentes no Supabase com runs, tasks, artifacts, events, checkpoints e memories;
- Etapa 4: ApprovalGate fail-closed e Publisher preparado, com persistência de approvals/publications e tradução de payload para Metricool;
- Etapa 5: contratos de mídia e renderer determinístico via FFmpeg, sem dependência obrigatória de voz;
- Etapa 6: QA automático de mídia, templates iniciais e ligação do SHA-256 do vídeo ao payload de aprovação;
- Etapa 7: fila persistente e idempotente, scheduler recorrente, claim concorrente seguro, retries com backoff, heartbeat, recuperação de jobs órfãos e ponte de retomada por checkpoint.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana deve pertencer ao mesmo `run_id` e ao payload exato;
- qualquer alteração do conteúdo ou da mídia invalida a autorização anterior;
- o Publisher exige autorização explícita de execução além da aprovação;
- jobs externos devem ser idempotentes sempre que possível;
- autonomia operacional não pode atravessar a barreira de aprovação;
- segredos ficam fora do Git.

## O que a Etapa 7 resolve
- concorrência entre workers com `FOR UPDATE SKIP LOCKED`;
- trabalho duplicado por meio de `idempotency_key`;
- falhas transitórias com retry/backoff;
- worker interrompido com heartbeat e requeue de stale job;
- agenda recorrente que materializa jobs sem executar lógica de agente dentro do banco;
- checkpoint retomável convertido em job de recovery.

## Limites atuais
- não há processo Worker hospedado 24/7; a biblioteca está pronta, mas o runtime seguro ainda precisa ser escolhido/conectado;
- o executor específico de cada pipeline precisa ser registrado no Worker, inclusive o executor de `run.resume`;
- publicação real continua deliberadamente bloqueada até aprovação + autorização explícita;
- Reviewer de mídia ainda não faz compreensão visual semântica quadro a quadro;
- dashboard operacional ainda não existe.

## Próximo passo
Etapa 8 recomendada: runtime operacional/observabilidade — hospedar o Worker, registrar handlers dos pipelines, adicionar métricas/notificações e construir uma visão simples da fila/runs antes do dashboard completo.
