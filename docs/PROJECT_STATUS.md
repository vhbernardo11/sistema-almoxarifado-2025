# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapas 1–9: consolidação, núcleo textual, memória Supabase, aprovação/Publisher, mídia, QA, autonomia, runtime hospedado test-only e dashboard operacional.
- Etapa 10 — implementação estrutural: claim RPC sintético, Edge Function agentic, fila de aprovação no dashboard e runtime Python com ApprovalGate.

## Etapa 10 — homologação adiada
A chave criada pelo fluxo seguro do ChatGPT existe na conta OpenAI, mas não foi injetada no ambiente das Supabase Edge Functions. O health check retorna `openai_key_present=false`.

Por decisão explícita do usuário, essa homologação fica em aberto e deixa de bloquear o avanço estrutural. Nenhum job real de IA será executado enquanto o secret não estiver disponível no runtime.

## Etapa 11 — em implementação
Objetivo: introduzir um Maestro determinístico e um catálogo canônico de especialistas, permitindo que o sistema planeje diferentes tipos de trabalho sem depender de execução ao vivo de modelo.

Rotas previstas:
- campanha;
- software;
- comercial;
- jurídico;
- SEO;
- analytics;
- operações.

Cada especialista declara estado (`implemented`, `prepared`, `blocked`) e efeito externo. O Publisher permanece fora de todas as rotas automáticas.

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

## Próximo marco da Etapa 11
1. consolidar contratos do Maestro e dos especialistas;
2. validar roteamento determinístico com testes;
3. registrar claramente capacidades ainda apenas preparadas;
4. manter Publisher e demais efeitos externos fora do planejamento automático;
5. só depois decidir quais especialistas receberão executores reais.
