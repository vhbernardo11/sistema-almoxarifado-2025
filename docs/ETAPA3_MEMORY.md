# Etapa 3 — Memória e estado persistente

Status: implementada e aplicada no projeto Supabase `Integrai Demo`.

## Objetivo

Fazer o IntegraSquad deixar de depender da duração de uma sessão. Cada execução passa a poder registrar tarefas, resultados, eventos, checkpoints e memória estruturada.

## Tabelas canônicas

- `squad_runs`: uma execução do sistema;
- `squad_tasks`: tarefas ordenadas por agente;
- `squad_artifacts`: referência a arquivos e outros artefatos;
- `squad_events`: histórico append-only do que aconteceu;
- `squad_checkpoints`: snapshots de retomada;
- `squad_memories`: fatos/preferências estruturados por escopo e chave.

As tabelas usam o prefixo `squad_` para não interferir nas tabelas existentes do IntegraTrampo/Integrai.

## Segurança

RLS está habilitado em todas as tabelas do IntegraSquad e nenhuma policy para `anon`/`authenticated` foi criada nesta etapa. Isso é intencional: o acesso operacional será exclusivamente de backend com `SUPABASE_SERVICE_ROLE_KEY`. Essa chave nunca deve ser enviada ao navegador nem commitada.

O advisor do Supabase reporta `rls_enabled_no_policy` como INFO; para estas seis tabelas, o bloqueio por ausência de policy é o comportamento desejado nesta fase.

## Integração Python

`SupabaseMemoryStore` implementa persistência real. `InMemoryMemoryStore` oferece a mesma interface para testes sem rede.

`run_text_core_persistent(...)` envolve o núcleo da Etapa 2 e grava automaticamente:

1. run;
2. três tasks (researcher, strategist, copywriter);
3. eventos de início/conclusão/falha;
4. checkpoint após cada saída validada;
5. snapshot final apontando `human_approval` como próxima etapa;
6. `publication_authorized=false` em todo o fluxo.

## Retomada

`get_resume_state(run_id)` retorna o último checkpoint, sequência de retomada, tarefas concluídas e não concluídas. A execução automática a partir desse checkpoint será usada na camada de autonomia; nesta etapa, o dado necessário para retomada já é persistido.

## Validação real do banco

Foi aplicado um smoke test direto no Supabase criando temporariamente um run, uma task, um artefato, um evento, um checkpoint e uma memória. Todos foram lidos com sucesso e removidos ao final; nenhuma linha de teste ficou no banco.
