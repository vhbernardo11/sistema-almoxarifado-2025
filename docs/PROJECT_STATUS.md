# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapas 1–9: consolidação, núcleo textual, memória Supabase, aprovação/Publisher, mídia, QA, autonomia, runtime hospedado test-only e dashboard operacional.
- Etapa 10 — implementação estrutural: claim RPC sintético, Edge Function agentic, fila de aprovação no dashboard e runtime Python com ApprovalGate.
- Etapa 11 — Maestro determinístico, catálogo canônico e roteamento por tipo de trabalho.
- Etapa 12 — primeira onda de especialistas determinísticos operacionais.

## Etapa 10 — homologação adiada
A chave criada pelo fluxo seguro do ChatGPT existe na conta OpenAI, mas não foi injetada no ambiente das Supabase Edge Functions. O health check retorna `openai_key_present=false`.

Por decisão explícita do usuário, essa homologação fica em aberto e deixa de bloquear o avanço estrutural. Nenhum job real de IA será executado enquanto o secret não estiver disponível no runtime.

O job sintético pendente da Etapa 10 foi cancelado para evitar execução futura acidental.

## Etapa 11 — concluída
O Maestro classifica pedidos em campanha, software, comercial, jurídico, SEO, analytics e operações. Publisher permanece fora das rotas automáticas e todos os planos nascem com publicação e efeitos externos não autorizados.

## Etapa 12 — concluída
Foram adicionados executores determinísticos para Programmer, Tester, Commercial, Legal Reviewer, SEO Analyst e Analytics.

Todos os executores da Etapa 12:
- exigem `test_mode=true`;
- aceitam apenas atores `stage8-test-*`;
- bloqueiam `publication_authorized=true`;
- bloqueiam `external_actions_authorized=true`;
- operam somente sobre payload fornecido;
- não enviam mensagens, não publicam, não fazem deploy e não modificam sistemas externos.

Capacidades principais:
- Programmer aplica operações declarativas em workspace virtual;
- Tester valida workspace sem executar código arbitrário;
- Commercial estrutura abordagem sem inventar provas;
- Legal Reviewer faz triagem e sempre exige revisão humana;
- SEO Analyst gera pacote on-page sem fingir dados de SERP;
- Analytics calcula deltas e funil apenas com métricas fornecidas.

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
- planos do Maestro sempre nascem com `publication_authorized=false` e `external_actions_authorized=false`;
- executores da Etapa 12 não possuem efeitos externos.

## Próximo marco possível
Uma etapa futura pode conectar esses especialistas ao runtime persistente e ao dashboard, mantendo usuários sintéticos, ou ampliar a segunda onda de capacidades. A homologação agentic da Etapa 10 continua separada e opcional.
