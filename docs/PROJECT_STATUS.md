# Status do projeto — 2026-09-10

## Fonte de verdade
Este repositório é o ponto canônico a partir da reconstrução.

## Confirmado e preservado
- contexto e arquitetura originais;
- roadmap e histórico da primeira tentativa;
- regra de aprovação humana antes de publicação;
- núcleo textual Researcher -> Strategist -> Copywriter reconstruído com saídas estruturadas;
- memória/estado persistente aplicada no Supabase `Integrai Demo`;
- tabelas para runs, tasks, artifacts, events, checkpoints e memories;
- checkpoints e `ResumeState` ligados ao núcleo textual;
- smoke test real de escrita/leitura/remoção executado no banco;
- testes automatizados do GitHub Actions aprovados;
- decisão de usar Python + OpenAI Agents SDK no núcleo textual;
- Metricool como candidato já experimentado para publicação;
- aprendizados de imagem, vídeo e voz registrados como experimentais.

## Segurança confirmada
- RLS habilitado em todas as seis tabelas `squad_*`;
- nenhuma policy pública criada nesta fase;
- acesso operacional previsto exclusivamente pelo backend com service-role key;
- segredos não são commitados;
- `publication_authorized=false` continua sendo invariante do núcleo textual.

## Limite atual da retomada
O sistema já persiste o dado necessário para descobrir onde uma execução parou. A retomada automática, retries e scheduler ainda não estão implementados; isso pertence à futura camada de autonomia.

## Experimental, não canônico
Nas sessões anteriores foram prototipados Designer, Videomaker, Revisor e checkpoint humano. Também houve renders locais de PNG/MP4 e tentativas de voz.

## O que não deve ser afirmado como pronto
- agentes rodando 24/7 em produção;
- retomada automática/retry sem operador;
- Publisher integrado no IntegraSquad;
- pipeline de mídia premium e confiável;
- dashboard;
- recuperação automática de falhas.

## Próxima etapa
Preparar aprovação humana e Publisher com trava fail-closed. Implementar essa etapa não significa autorizar nem executar uma publicação externa.
