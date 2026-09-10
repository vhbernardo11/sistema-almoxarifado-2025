# Status do projeto — 2026-09-10

## Fonte de verdade
Este repositório é o ponto canônico a partir da reconstrução.

## Confirmado e preservado
- contexto e arquitetura originais;
- roadmap de 12 etapas da primeira tentativa;
- contratos-base `Run`, `Task`, `AgentResult` e `Artifact`;
- regra de aprovação humana antes de publicação;
- decisão de usar Python + OpenAI Agents SDK no núcleo textual;
- decisão de usar Supabase para memória/estado;
- Metricool como candidato já experimentado para publicação;
- aprendizados de imagem, vídeo e voz registrados como experimentais.

## Experimental, não canônico
Nas sessões anteriores foram prototipados Maestro, Pesquisador, Estrategista, Copywriter, Designer, Videomaker, Revisor e checkpoint humano. Também houve renders locais de PNG/MP4 e tentativas de voz.

Esses experimentos provaram partes do desenho, mas não são considerados produção porque dependeram de sessões/ambientes temporários e integrações inconsistentes.

## O que não deve ser afirmado como pronto
- agentes rodando 24/7 em produção;
- memória persistente no Supabase;
- Publisher integrado no IntegraSquad;
- pipeline de mídia premium e confiável;
- dashboard;
- recuperação automática de falhas.

## Próxima etapa
Reconstruir o núcleo textual limpo, no repositório canônico, sem dependência de mídia.
