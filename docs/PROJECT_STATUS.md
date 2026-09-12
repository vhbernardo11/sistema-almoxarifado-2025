# Status do projeto — 2026-09-12

## Fonte de verdade
Este repositório é o ponto canônico do IntegraSquad.

## Concluído
- Etapas 1–9: fundação, agentes textuais, persistência, aprovação, mídia, QA, autonomia, runtime e dashboard.
- Etapa 11: Maestro e catálogo de especialistas.
- Etapa 12: primeira onda com Programmer, Tester, Commercial, Legal Reviewer, SEO Analyst e Analytics.
- Etapa 13: integração da primeira onda com `squad_jobs`, worker hospedado test-only e Sala de Controle.
- Etapa 14: segunda onda determinística (Researcher, Strategist, Copywriter, Reviewer) + workflow sequencial `maestro.workflow` executado por worker hospedado.

## Etapa 10 — em aberto
A homologação ao vivo do runtime agentic continua adiada por decisão do usuário. A ausência de `OPENAI_API_KEY` no Edge Runtime não bloqueia os executores determinísticos das Etapas 12–14.

## Etapa 14
O Maestro agora pode executar rotas completas em modo determinístico, desde que cada especialista receba um payload explícito. Saídas anteriores podem alimentar passos seguintes por referência estruturada.

Homologação viva concluída exclusivamente com `stage8-test-user-001`:
- campaign: Researcher -> Strategist -> Copywriter -> Reviewer;
- software: Researcher -> Programmer -> Tester -> Reviewer;
- ambos concluídos na primeira tentativa;
- Tester validou com sucesso o workspace produzido pelo Programmer;
- Reviewer encaminhou ambos para revisão humana;
- 0 falhas no tick de homologação.

Runtime:
- Edge Function `integrasquad-stage14-worker` ativa;
- cron `integrasquad-stage14-maestro-worker` ativo a cada 5 minutos;
- dashboard responde `stage=14` e mostra workflows do Maestro;
- 0 publicações criadas durante a homologação da Etapa 14.

## Invariantes
- usuários reais ficam fora da homologação;
- `test_mode=true` em todo workflow;
- `publication_authorized=false` em todo workflow e resultado;
- `external_actions_authorized=false` em todo workflow e resultado;
- Publisher não participa de rotas automáticas;
- alteração externa não é executada por especialistas determinísticos;
- Researcher da Etapa 14 não faz navegação/pesquisa externa;
- Legal Reviewer continua sendo triagem e exige humano;
- Reviewer sempre termina na barreira humana;
- Programmer trabalha apenas em workspace virtual;
- Etapa 10 agentic permanece separada e opcional.
