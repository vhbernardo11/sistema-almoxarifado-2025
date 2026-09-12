# Status do projeto — 2026-09-12

## Fonte de verdade
Este repositório é o ponto canônico do IntegraSquad.

## Concluído
- Etapas 1–9: fundação, agentes textuais, persistência, aprovação, mídia, QA, autonomia, runtime e dashboard.
- Etapa 11: Maestro e catálogo de especialistas.
- Etapa 12: primeira onda com Programmer, Tester, Commercial, Legal Reviewer, SEO Analyst e Analytics.
- Etapa 13: integração da primeira onda com `squad_jobs`, worker hospedado test-only e Sala de Controle.
- Etapa 14: segunda onda determinística + workflow sequencial `maestro.workflow`.
- Etapa 15: workflow durável `maestro.workflow.v2`, ledger por etapa, retomada após interrupção e visualização do progresso na Sala de Controle.

## Etapa 10 — em aberto
A homologação ao vivo do runtime agentic continua adiada por decisão do usuário. A ausência de `OPENAI_API_KEY` no Edge Runtime não bloqueia os executores determinísticos das Etapas 12–15.

## Etapa 15
Novas estruturas:
- `squad_workflows` — estado agregado, posição atual e guardrails;
- `squad_workflow_steps` — checkpoint, entrada, saída, tentativa e erro de cada especialista;
- `maestro.workflow.v2` — job durável;
- `integrasquad-stage15-worker` — Edge Function test-only;
- `integrasquad-stage15-durable-worker` — cron a cada 5 minutos.

Homologação viva, exclusivamente com `stage8-test-user-001`:
- workflow de software iniciado;
- interrupção sintética depois de Researcher + Programmer;
- estado persistido em `retry`, `current_step=2`, 2/4 etapas;
- segunda execução retomou no Tester, sem repetir Researcher/Programmer;
- Tester validou JSON;
- Reviewer encerrou em `needs_review`;
- 4/4 etapas registradas com `attempt=1`;
- resultado final registrou `resumed_from_step=2`;
- 0 publicações criadas.

## Invariantes
- usuários reais ficam fora da homologação;
- `test_mode=true` obrigatório;
- `publication_authorized=false` em jobs, workflows, resultados e CHECK do banco;
- `external_actions_authorized=false` em jobs, workflows, resultados e CHECK do banco;
- RLS habilitado em `squad_workflows` e `squad_workflow_steps`;
- `anon` e `authenticated` sem acesso direto às tabelas novas;
- Publisher não participa de rotas automáticas;
- alteração externa não é executada por especialistas determinísticos;
- Researcher determinístico não navega na web;
- Legal Reviewer continua sendo triagem e exige humano;
- Reviewer termina na barreira humana;
- Programmer trabalha apenas em workspace virtual;
- Etapa 10 agentic permanece separada e opcional.
