# Etapa 4 — Aprovação humana + Publisher preparado

## Objetivo
Impedir qualquer publicação externa sem aprovação humana explícita e preparar o Publisher para registrar o ciclo de publicação sem publicar nada nesta etapa.

## Fail closed
A aprovação fica vinculada ao `run_id` e ao SHA-256 do payload canônico. Se o conteúdo mudar depois da aprovação, a publicação volta a ser bloqueada. A aprovação também não pode ser reutilizada em outra execução.

Há duas travas distintas:
1. `decision == approved` para o payload exato;
2. `execution_authorized=True` no momento de uma futura chamada externa.

## Persistência
O Supabase usa `squad_approvals` e `squad_publications`. `prepare()` pode registrar uma publicação como `prepared` sem qualquer ação externa. Sucesso e falha do provedor também têm estados persistíveis.

As tabelas têm RLS habilitado e não concedem SELECT a `anon` nem `authenticated`; o acesso previsto é server-side.

## Metricool
O conector desta conta foi inspecionado. O brand detectado é `vhbernardo`, id `6864168`, timezone `America/Sao_Paulo`.

O conector oferece agendamento/publicação e fluxo de revisão. Nesta etapa NÃO foi criado, agendado nem publicado post algum. O código inclui `MetricoolPayloadBuilder`; a chamada externa continua atrás do `PublisherService` e do `ApprovalGate`.

## Testes
Os testes cobrem bloqueio para pending/changes_requested/rejected, aprovação do payload exato, invalidação após mudança, isolamento por run, preparação sem ação externa, segunda autorização explícita, persistência de sucesso e persistência de falha.
