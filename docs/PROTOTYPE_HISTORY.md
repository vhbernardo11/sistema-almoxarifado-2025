# Histórico do protótipo anterior

Este documento preserva o que foi feito antes da reconstrução, sem promover código experimental a produção.

## Etapa 1 — Fundação
Foi criado um starter Python com Pydantic, dotenv, pytest, contratos de Run/Task/AgentResult/Artifact e smoke test.

## Etapa 2 — Maestro
Foi prototipado um coordenador capaz de devolver planos estruturados e preservar a ordem de aprovação humana antes do Publisher.

## Etapa 3 — Núcleo textual
Foram prototipados Pesquisador, Estrategista e Copywriter, com saídas estruturadas e dry-runs. A execução real via Agents SDK ficou limitada pelo ambiente temporário e pela indisponibilidade da chave dentro do sandbox.

## Etapa 4 — Designer
Foi prototipado o contrato visual 9:16 e, depois, um renderer local determinístico de PNG para fechar a lacuna técnica entre brief e arquivo.

## Etapa 5 — Videomaker
Foi prototipado um pacote de shots e depois um renderer local de MP4 via FFmpeg. Isso gerou arquivo real, mas não movimento de personagem nem qualidade premium.

## Etapa 6 — Revisor
Foi prototipada uma camada de QA estrutural para profissão, marca, CTA, claims, formato e existência de mídia.

## Etapa 7 — Aprovação humana
Foi prototipado um checkpoint com `approve`, `request_changes` e `discard`, mantendo o Publisher inativo até decisão humana.

## Principal aprendizado
O núcleo multiagente evoluiu melhor que a camada de mídia. O projeto começou a acumular remendos ao misturar raciocínio, render local, TTS, plugins e serviços externos. A reconstrução separa o núcleo do produto dos providers de execução.
