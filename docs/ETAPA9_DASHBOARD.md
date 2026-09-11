# Etapa 9 — Painel operacional de teste

A Etapa 9 cria uma sala de controle **somente leitura** para acompanhar a autonomia do IntegraSquad sem tocar usuários reais.

## Escopo

- Edge Function `integrasquad-stage9-dashboard` hospedada no Supabase;
- visão de saúde do runtime, fila, retries, falhas, espera por aprovação, ticks e alertas;
- atualização automática no navegador;
- endpoint JSON da mesma visão para futuras interfaces;
- domínio Python `integra.dashboard` com filtro obrigatório de atores sintéticos;
- nenhuma ação de escrita, publicação, mensagem ou mutação exposta no painel.

## Regra de teste

O dashboard só mostra jobs cujo `payload.test_mode=true` e cujo `payload.test_actor_id` começa com `stage8-test-`. Ticks precisam carregar `detail.test_only=true`; alertas e atores também são filtrados pelo prefixo sintético.

O endpoint é público apenas porque os dados retornados são sintéticos e read-only. A Service Role permanece dentro do ambiente da Edge Function e nunca é enviada ao navegador.

## Saúde

O runtime é considerado `healthy` quando existe tick de teste concluído nos últimos 12 minutos. Sem ticks ele fica `idle`; tick antigo ou condição anormal vira `degraded`.

## Aprovação humana

O painel pode exibir que um job está esperando aprovação, mas não oferece botão de publicar. `publication_authorized=false` continua preservado e o Publisher permanece fora do runtime automático.
