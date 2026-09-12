# Etapa 13 — Especialistas na fila, runtime e Sala de Controle

A Etapa 13 conecta os executores determinísticos da Etapa 12 à infraestrutura operacional construída nas Etapas 7–9.

## O que entra na fila

Os seis especialistas agora possuem `job_type` próprio:

- `specialist.programmer`
- `specialist.tester`
- `specialist.commercial`
- `specialist.legal_reviewer`
- `specialist.seo_analyst`
- `specialist.analytics`

`enqueue_specialist_task` transforma um `SpecialistTask` em job persistível e idempotente.

## Runtime Python

`build_stage8_handlers` registra os seis tipos e encaminha cada job para `execute_specialist_job`, preservando os contratos da Etapa 12.

## Runtime hospedado

A Edge Function `integrasquad-stage13-worker` usa RPCs próprias para reclamar apenas jobs `specialist.%`. Um cron independente a chama a cada cinco minutos, sem competir com o worker antigo de `test.%` nem com a Etapa 10.

O runtime continua exigindo:

- `test_mode=true`;
- ator `stage8-test-*`;
- token interno do worker;
- `publication_authorized=false`;
- `external_actions_authorized=false`.

## Sala de Controle

O endpoint de dashboard expõe uma coleção `specialists` com especialista, status do job, status do resultado, ator sintético, necessidade de revisão humana e horário da última atualização. A página pública continua somente leitura.

## Limites intencionais

- nenhum job usa usuário real;
- nenhum especialista publica ou envia mensagens;
- Programmer continua em workspace virtual;
- Tester hospedado não executa Python; `python_compile` continua canônico no runtime Python;
- a Etapa 10 continua adiada e não é pré-requisito para estes executores determinísticos.
