# Etapa 8 — Runtime operacional de teste e observabilidade

A Etapa 8 coloca uma parte real da camada autônoma em execução contínua, mas sob um perímetro deliberadamente **test-only**.

## Regra central

Nenhum teste desta etapa usa usuário real. Os únicos atores aceitos pelo runtime operacional são IDs com prefixo `stage8-test-`, cadastrados em `squad_test_actors` e usando e-mails do domínio reservado `example.invalid`.

A Edge Function também só faz claim de jobs `test.*` cujo payload tenha `test_mode=true` e um ator de teste habilitado. Jobs reais ou jobs de publicação não entram nesse runtime.

## Runtime hospedado

Foi implantada a Supabase Edge Function `integrasquad-stage8-worker` no projeto Integrai Demo. Ela é chamada pelo `pg_cron` a cada 5 minutos.

A função não depende de uma chave escrita no Git. O cron usa um token interno aleatório criado no Supabase Vault. A Edge Function valida o header por meio da RPC `squad_verify_stage8_worker_token` antes de tocar na fila.

## Observabilidade

Novas estruturas:

- `squad_test_actors`: identidades sintéticas autorizadas na Etapa 8;
- `squad_runtime_ticks`: telemetria de cada invocação do worker;
- `squad_runtime_alerts`: alertas internos de falha ou espera por aprovação.

Cada tick registra jobs reclamados, concluídos, colocados em retry, falhas, schedules materializados e jobs stale recuperados.

## Handlers

O runtime Edge hospedado executa apenas handlers sintéticos seguros:

- `test.echo`;
- `test.retry_once`;
- `test.waiting_approval`;
- `test.fail`.

O runtime Python canônico (`src/integra/runtime`) também registra os adapters reais `text_core.run` e `media.review`, sempre protegidos pelo guard de usuário de teste. `publisher.execute` **não é registrado**.

## Teste end-to-end realizado

Foram enfileirados somente usuários de teste:

- `stage8-test-user-001`;
- `stage8-test-admin-001`.

Resultados observados no Supabase real:

1. `test.echo` foi concluído na primeira tentativa;
2. `test.retry_once` falhou de forma sintética, entrou em `retry` e no tick seguinte do cron foi concluído na segunda tentativa;
3. `test.waiting_approval` terminou com `publication_authorized=false` e gerou um alerta interno `waiting_approval`.

Nenhuma publicação, mensagem, post, contato com cliente ou ação externa de produção foi realizada.

## Limites

- O runtime 24/7 hospedado nesta etapa é propositalmente test-only.
- Os handlers Python de `text_core.run` e `media.review` estão conectados no código, mas ainda não são executados pela Edge Function Deno.
- O Publisher continua fora do runtime automático.
- Alertas são internos no banco; não há notificação externa automática nesta etapa.

## Próximo passo natural

A próxima etapa pode criar uma visão operacional/dashboard de fila, runs, ticks, alertas e aprovações, ou promover gradualmente handlers reais para um runtime backend com segredos apropriados, mantendo o modo de teste como padrão até validação explícita.
