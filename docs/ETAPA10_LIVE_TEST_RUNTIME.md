# Etapa 10 — runtime agentic de homologação

## Objetivo

Promover o núcleo textual `Researcher -> Strategist -> Copywriter` para um runtime hospedado, mantendo **somente usuários sintéticos** e a barreira humana de publicação.

## Perímetro de teste

O runtime Stage 10 só pode reclamar `text_core.run` quando:

- `payload.test_mode = true`;
- `payload.test_actor_id` começa com `stage8-test-`;
- o ator existe e está habilitado em `squad_test_actors`;
- o job está `pending` ou `retry`.

O RPC `squad_claim_next_stage10_test_job` é `SECURITY DEFINER`, usa `FOR UPDATE SKIP LOCKED` e só é executável por `service_role`.

## Execução hospedada

A Edge Function `integrasquad-stage10-runtime`:

1. valida o token interno do worker;
2. recusa executar sem `OPENAI_API_KEY` no ambiente da função;
3. reclama um job sintético `text_core.run`;
4. executa Researcher com web search e saída estruturada;
5. executa Strategist e Copywriter com JSON Schema estrito;
6. persiste run, tasks, events e checkpoints;
7. cria uma aprovação humana `pending` para o payload exato;
8. grava `publication_authorized=false` no resultado;
9. nunca registra nem executa Publisher.

Modelo de homologação configurado: `gpt-5.6-luna`.

## Fila de aprovação

O dashboard da Etapa 9 foi ampliado para ler `squad_approvals` e mostrar somente registros cujo `metadata.test_mode=true` e `metadata.test_actor_id` seja `stage8-test-*`.

A fila é somente leitura. Não há botão de aprovar, publicar, enviar mensagem ou alterar job.

## Estado da credencial

A chave criada pelo fluxo seguro do ChatGPT não é injetada automaticamente no Supabase Edge Runtime. Enquanto `OPENAI_API_KEY` não estiver configurada nos secrets do projeto Supabase, o endpoint retorna `openai_key_present=false` e **não reclama nenhum job**. Isso mantém a homologação segura e evita execução parcial.

## Critérios para considerar a Etapa 10 operacional

- CI determinístico aprovado;
- Edge Function e RPC ativos;
- dashboard mostrando a fila de aprovação sintética;
- `OPENAI_API_KEY` presente no runtime;
- uma execução real com `stage8-test-user-001` concluída em `waiting_approval`;
- nenhuma publicação externa.
