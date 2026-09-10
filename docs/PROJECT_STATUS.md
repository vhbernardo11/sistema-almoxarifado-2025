# Status do projeto — 2026-09-10

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapa 1: consolidação persistente no GitHub;
- Etapa 2: núcleo textual estruturado Researcher -> Strategist -> Copywriter;
- Etapa 3: memória/estado persistentes no Supabase com runs, tasks, artifacts, events, checkpoints e memories;
- Etapa 4: ApprovalGate fail-closed e Publisher preparado, com persistência de approvals/publications e tradução de payload para Metricool;
- Etapa 5: contratos de mídia e renderer determinístico via FFmpeg, sem dependência obrigatória de voz;
- Etapa 6: QA automático de mídia, templates iniciais e ligação do SHA-256 do vídeo ao payload de aprovação.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana deve pertencer ao mesmo `run_id` e ao payload exato;
- o SHA-256 do vídeo faz parte do payload aprovado;
- qualquer alteração do conteúdo ou da mídia invalida a autorização anterior;
- o Publisher exige autorização explícita de execução além da aprovação;
- segredos ficam fora do Git;
- integrações externas são adaptadores, não lógica embutida nos agentes.

## Limites atuais
- o Reviewer da Etapa 6 valida artefato e metadados, não compreensão visual quadro a quadro;
- publicação real automatizada pelo IntegraSquad ainda não é executada;
- voz premium confiável ainda não integra o pipeline;
- fila/scheduler/retry autônomo ainda não existe;
- dashboard operacional ainda não existe.

## Próximo passo
Etapa 7 recomendada: camada de execução autônoma com fila, scheduler, retry, retomada de checkpoints e notificações, mantendo publicação fail-closed.
