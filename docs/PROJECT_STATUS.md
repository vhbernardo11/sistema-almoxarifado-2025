# Status do projeto — 2026-09-10

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapa 1: consolidação persistente no GitHub;
- Etapa 2: núcleo textual estruturado Researcher -> Strategist -> Copywriter;
- Etapa 3: memória/estado persistentes no Supabase com runs, tasks, artifacts, events, checkpoints e memories;
- Etapa 4: ApprovalGate fail-closed e Publisher preparado, com persistência de approvals/publications e tradução de payload para Metricool.

## Invariantes
- nenhum agente textual publica conteúdo;
- aprovação humana deve pertencer ao mesmo `run_id` e ao payload exato;
- qualquer alteração do conteúdo invalida a autorização anterior;
- o Publisher exige autorização explícita de execução além da aprovação;
- segredos ficam fora do Git;
- integrações externas são adaptadores, não lógica embutida nos agentes.

## Não concluído ainda
- publicação real automatizada pelo IntegraSquad;
- imagem/vídeo premium confiável;
- fila/scheduler/retry autônomo;
- dashboard operacional.

## Próximo passo
Voltar para mídia somente depois da validação do núcleo operacional. A Etapa 5 tratará imagem/vídeo sem enfraquecer as travas de aprovação existentes.
