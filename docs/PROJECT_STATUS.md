# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapas 1–9: consolidação, núcleo textual, memória Supabase, aprovação/Publisher, mídia, QA, autonomia, runtime hospedado test-only e dashboard operacional.
- Etapa 10 — implementação estrutural: claim RPC sintético, Edge Function agentic, fila de aprovação no dashboard e runtime Python com ApprovalGate.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana pertence ao mesmo `run_id` e payload exato;
- alteração de conteúdo ou mídia invalida autorização anterior;
- Publisher exige autorização explícita além da aprovação;
- jobs externos devem ser idempotentes sempre que possível;
- autonomia operacional não atravessa a barreira de aprovação;
- segredos ficam fora do Git;
- homologação usa somente usuários `stage8-test-*`.

## Etapa 10
O novo runtime hospedado aceita somente `text_core.run` sintético. Ele foi desenhado para executar Researcher com web search, depois Strategist e Copywriter com saída estruturada, persistir tasks/events/checkpoints e criar `squad_approvals` em `pending`, sempre com `publication_authorized=false`.

A Sala de Controle agora também possui fila de aprovação humana somente leitura, filtrada por `metadata.test_mode=true` e `stage8-test-*`.

## Bloqueio atual de credencial
A chave criada pelo fluxo seguro do ChatGPT existe na conta OpenAI, mas não é injetada automaticamente no ambiente das Supabase Edge Functions. O health check da Etapa 10 retorna `openai_key_present=false`. Por segurança, o runtime verifica isso **antes de reclamar qualquer job**.

Portanto, a Etapa 10 está implementada e pronta para homologação ao vivo, mas a primeira execução real do modelo só pode ocorrer depois que `OPENAI_API_KEY` for configurada como secret no projeto Supabase.

## Próximo marco dentro da própria Etapa 10
1. configurar `OPENAI_API_KEY` no Edge Runtime sem expor o valor;
2. confirmar health `openai_key_present=true`;
3. processar um único `text_core.run` de `stage8-test-user-001`;
4. confirmar aprovação `pending`, `publication_authorized=false` e visibilidade no dashboard;
5. não publicar nada.

Nenhuma Etapa 11 deve começar antes da conclusão dessa homologação e de nova autorização do usuário.
