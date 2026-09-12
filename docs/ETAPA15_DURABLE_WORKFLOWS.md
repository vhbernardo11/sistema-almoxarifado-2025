# Etapa 15 — Workflows duráveis e retomáveis

A Etapa 15 transforma o workflow multi-especialista da Etapa 14 em uma execução durável, com checkpoint persistente por especialista.

## Objetivo

Se o worker for interrompido depois de algumas etapas, a próxima execução retoma do primeiro passo ainda não concluído. Etapas concluídas não são executadas novamente.

## Componentes

- `maestro.workflow.v2`: novo tipo de job durável.
- `squad_workflows`: estado agregado do workflow, progresso e barreiras de segurança.
- `squad_workflow_steps`: ledger de cada especialista, entrada, saída, tentativa e erro.
- `integrasquad-stage15-worker`: worker hospedado test-only.
- `squad_claim_next_stage15_workflow_job`: claim atômico exclusivo para v2.
- `squad_requeue_stale_stage15_workflow_jobs`: recuperação de worker sem heartbeat.
- `squad_invoke_stage15_test_worker`: invocador interno seguro para homologação.
- cron `integrasquad-stage15-durable-worker`: execução a cada 5 minutos.

## Segurança

A etapa continua exclusivamente em homologação:

- `test_mode=true` obrigatório;
- somente atores `stage8-test-*` habilitados;
- `publication_authorized=false` com CHECK no banco;
- `external_actions_authorized=false` com CHECK no banco;
- Publisher não é chamado;
- RLS habilitado e acesso de `anon`/`authenticated` revogado nas tabelas novas.

## Homologação real

Foi criado um job sintético de software com interrupção controlada após o Programmer. Na primeira execução foram persistidos Researcher e Programmer e o job ficou em `retry`, com `current_step=2`. Na segunda execução, o worker retomou diretamente no Tester e Reviewer. Cada especialista apareceu apenas uma vez no ledger (`attempt=1`), comprovando que as etapas concluídas não foram repetidas.

Resultado final:

- 4/4 etapas concluídas;
- Tester validou JSON com sucesso;
- Reviewer marcou `needs_review`;
- `resumed_from_step=2`;
- publicação e efeitos externos permaneceram bloqueados.
