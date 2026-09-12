# Etapa 14 — Maestro workflows multi-especialista

## Objetivo
Conectar o Maestro a um workflow determinístico sequencial, mantendo homologação exclusiva com usuários sintéticos e bloqueio total de publicação/efeitos externos.

## Segunda onda de especialistas
Foram adicionados executores determinísticos para:
- Researcher: organiza fatos/fontes fornecidos; não faz pesquisa externa;
- Strategist: estrutura objetivo, público, prioridades e guardrails;
- Copywriter: produz headline/legenda/CTA somente a partir do payload;
- Reviewer: valida campos/flags e sempre exige revisão humana.

Eles se somam a Programmer, Tester, Commercial, Legal Reviewer, SEO Analyst e Analytics.

## Workflow do Maestro
Job type: `maestro.workflow`.

O payload contém:
- `test_mode=true`;
- `test_actor_id=stage8-test-*`;
- `work`: `WorkRequest` do Maestro;
- `step_payloads`: payload específico de cada especialista;
- `publication_authorized=false`;
- `external_actions_authorized=false`.

Referências entre etapas usam:
```json
{"$step":"programmer","path":"data.workspace"}
```

## Runtime hospedado
Edge Function: `integrasquad-stage14-worker`.

O worker:
1. autentica com o token interno já guardado no Vault;
2. reclama somente `maestro.workflow` de atores sintéticos habilitados;
3. executa as etapas em sequência;
4. persiste o resultado em `squad_jobs.result`;
5. gera alerta quando há revisão humana obrigatória;
6. nunca chama Publisher.

Cron: `integrasquad-stage14-maestro-worker`, a cada 5 minutos.

## Homologação ao vivo
Foram executados dois workflows sintéticos:
- `stage14-live-campaign-001`: campaign, 4 etapas, concluído em `needs_review`;
- `stage14-live-software-001`: software, 4 etapas, Tester recebeu o workspace do Programmer e retornou `passed=true`.

Ambos:
- concluíram na primeira tentativa;
- `publication_authorized=false`;
- `external_actions_authorized=false`;
- terminaram aguardando revisão humana.

O tick do worker hospedado concluiu 2/2 jobs e registrou 0 falhas.

## Dashboard
A API do dashboard agora retorna `stage=14`, `workflow_jobs` e a lista `workflows`. O painel estático mostra rota, status do job, status do workflow, quantidade de etapas, ator sintético, revisão humana e bloqueio de publicação.

## Limitações intencionais
- Researcher determinístico não substitui pesquisa web;
- Etapa 10 agentic continua separada/em aberto;
- payloads dos especialistas devem ser explícitos;
- Reviewer não aprova publicação;
- nenhuma rota contém Publisher.
