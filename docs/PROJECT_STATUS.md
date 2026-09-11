# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapas 1–9: consolidação, núcleo textual, memória Supabase, aprovação/Publisher, mídia, QA, autonomia, runtime hospedado test-only e dashboard operacional.
- Etapa 10 — implementação estrutural: claim RPC sintético, Edge Function agentic, fila de aprovação no dashboard e runtime Python com ApprovalGate.
- Etapa 11 — Maestro determinístico, catálogo canônico de especialistas, rotas estruturadas e bloqueio explícito de capacidades ainda não conectadas.

## Etapa 10 — homologação adiada
A chave criada pelo fluxo seguro do ChatGPT existe na conta OpenAI, mas não foi injetada no ambiente das Supabase Edge Functions. O health check retorna `openai_key_present=false`.

Por decisão explícita do usuário, essa homologação fica em aberto e deixa de bloquear o avanço estrutural. O job sintético de homologação que estava pendente foi marcado como `cancelled`, evitando execução futura acidental. Nenhum job real de IA será executado enquanto o secret não estiver disponível no runtime.

## Etapa 11 — concluída
O pacote `integra.maestro` transforma pedidos em planos estruturados e reproduzíveis para:
- campanha;
- software;
- comercial;
- jurídico;
- SEO;
- analytics;
- operações.

Cada especialista declara estado (`implemented`, `prepared`, `blocked`) e efeito externo. Rotas que dependem de capacidade ainda não implementada retornam `ready_for_execution=false` com bloqueios explícitos.

O Publisher permanece no catálogo apenas como componente arquitetural e não aparece em nenhuma rota automática. Mesmo quando o pedido informa `allow_external_actions=true`, o Maestro mantém `publication_authorized=false` e `external_actions_authorized=false`.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana pertence ao mesmo `run_id` e payload exato;
- alteração de conteúdo ou mídia invalida autorização anterior;
- Publisher exige autorização explícita além da aprovação;
- jobs externos devem ser idempotentes sempre que possível;
- autonomia operacional não atravessa a barreira de aprovação;
- segredos ficam fora do Git;
- homologação usa somente usuários `stage8-test-*`;
- planos do Maestro sempre nascem com `publication_authorized=false` e `external_actions_authorized=false`.

## Etapa 12 — não iniciada
Próximo objetivo proposto: conectar executores especializados um a um, começando pelas capacidades de maior utilidade prática, sem liberar efeitos externos automaticamente.

Nenhuma implementação da Etapa 12 deve começar sem nova autorização explícita do usuário.
