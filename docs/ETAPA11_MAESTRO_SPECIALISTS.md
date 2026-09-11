# Etapa 11 — Maestro e catálogo de especialistas

## Objetivo
Expandir o IntegraSquad para além do pipeline de marketing sem depender da homologação ao vivo da Etapa 10.

A Etapa 11 introduz um Maestro determinístico que transforma um pedido em um plano estruturado, seleciona especialistas por rota e mantém a barreira de publicação fechada.

## Escopo
- catálogo canônico de especialistas e capacidades;
- roteamento por tipo de trabalho;
- planejamento estruturado e reproduzível;
- indicação explícita de capacidades prontas ou ainda preparadas;
- Publisher fora de qualquer plano automático;
- `publication_authorized=false` e `external_actions_authorized=false` em todos os planos.

## Rotas iniciais
- `campaign`: Researcher -> Strategist -> Copywriter -> Reviewer
- `software`: Researcher -> Programmer -> Tester -> Reviewer
- `commercial`: Researcher -> Commercial -> Copywriter -> Reviewer
- `legal`: Researcher -> Legal Reviewer -> Reviewer
- `seo`: Researcher -> SEO Analyst -> Copywriter -> Reviewer
- `analytics`: Analytics -> Strategist -> Reviewer
- `operations`: Strategist -> Reviewer

## Estados de capacidade
- `implemented`: contrato e componente já existentes no repositório;
- `prepared`: papel e contrato definidos, mas executor especializado ainda não foi conectado;
- `blocked`: capacidade deliberadamente indisponível.

O Maestro não esconde lacunas. Se uma rota exigir uma capacidade `prepared` ou `blocked`, o plano nasce com `ready_for_execution=false` e lista os bloqueios.

## Regra de segurança
O Maestro pode planejar, mas não publica, não envia mensagens e não executa efeitos externos. Mesmo que o pedido contenha `allow_external_actions=true`, a Etapa 11 não autoriza Publisher.

O Publisher permanece no catálogo apenas para tornar a arquitetura explícita e exige fluxo separado com aprovação humana válida e autorização explícita.

## Etapa 10 adiada
A homologação ao vivo da Etapa 10 fica registrada como pendência deliberada. A falta de `OPENAI_API_KEY` no Edge Runtime não bloqueia o desenvolvimento estrutural da Etapa 11.
