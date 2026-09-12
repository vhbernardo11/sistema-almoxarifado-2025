# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico do IntegraSquad.

## Concluído
- Etapas 1–9: fundação, agentes textuais, persistência, aprovação, mídia, QA, autonomia, runtime e dashboard.
- Etapa 11: Maestro e catálogo de especialistas.
- Etapa 12: seis especialistas determinísticos.
- Etapa 13: integração desses especialistas com `squad_jobs`, worker test-only e Sala de Controle.

## Etapa 10 — em aberto
A homologação ao vivo do runtime agentic continua adiada por decisão do usuário. A ausência de `OPENAI_API_KEY` no Edge Runtime não bloqueia os executores determinísticos das Etapas 12–13.

## Etapa 13
Job types operacionais:
- `specialist.programmer`
- `specialist.tester`
- `specialist.commercial`
- `specialist.legal_reviewer`
- `specialist.seo_analyst`
- `specialist.analytics`

Todos exigem `test_mode=true` e ator `stage8-test-*`. O runtime registra resultados em `squad_jobs.result`; resultados que exigem revisão humana geram alerta informativo.

## Invariantes
- usuários reais ficam fora da homologação;
- `publication_authorized=false` em todo job especialista;
- `external_actions_authorized=false` em todo job especialista;
- Publisher não é handler do worker especialista;
- nenhuma mensagem, publicação, deploy ou alteração externa é feita por esses jobs;
- Legal Reviewer sempre exige humano;
- Programmer trabalha apenas em workspace virtual.
