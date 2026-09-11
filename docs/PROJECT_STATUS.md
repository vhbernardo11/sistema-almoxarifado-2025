# Status do projeto — 2026-09-11

## Fonte de verdade
Este repositório é o ponto canônico da reconstrução do IntegraSquad.

## Concluído
- Etapa 1: consolidação persistente no GitHub;
- Etapa 2: núcleo textual estruturado Researcher -> Strategist -> Copywriter;
- Etapa 3: memória/estado persistentes no Supabase com runs, tasks, artifacts, events, checkpoints e memories;
- Etapa 4: ApprovalGate fail-closed e Publisher preparado;
- Etapa 5: contratos de mídia e renderer determinístico via FFmpeg;
- Etapa 6: QA automático de mídia, templates e SHA-256 ligado à aprovação;
- Etapa 7: fila persistente, scheduler, retry/backoff, heartbeat e recuperação por checkpoint;
- Etapa 8: runtime hospedado test-only no Supabase Edge Functions, cron a cada 5 minutos, atores sintéticos, telemetria e alertas internos;
- Etapa 9: dashboard operacional web read-only com snapshot test-only de jobs, ticks, alertas, atores e espera por aprovação.

## Invariantes
- nenhum agente textual publica conteúdo;
- mídia com erro estrutural não chega à aprovação;
- aprovação humana pertence ao mesmo `run_id` e payload exato;
- alteração de conteúdo ou mídia invalida autorização anterior;
- o Publisher exige autorização explícita além da aprovação;
- jobs externos devem ser idempotentes sempre que possível;
- autonomia operacional não atravessa a barreira de aprovação;
- segredos ficam fora do Git;
- homologação usa somente usuários `stage8-test-*`;
- dashboard da Etapa 9 é somente leitura e não expõe ações mutáveis.

## O que a Etapa 9 resolve
- visão visual da saúde do runtime;
- contagem de jobs concluídos, pendentes, retries e falhas;
- identificação de jobs aguardando aprovação humana;
- histórico de ticks do worker e alertas internos;
- atualização automática no navegador;
- API JSON test-only para futuras interfaces;
- filtro duplo: `test_mode=true` e ator sintético `stage8-test-*`.

## Validação da Etapa 9
- Edge Function `integrasquad-stage9-dashboard` ativa;
- endpoint JSON respondeu HTTP 200;
- snapshot validado com 3 jobs sintéticos, todos concluídos;
- 1 job sintético continua marcado como `waiting_approval` e `publication_authorized=false`;
- runtime reportado como `healthy` com tick recente;
- nenhum usuário real apareceu no snapshot.

## Limites atuais
- runtime hospedado continua propositalmente test-only;
- handlers Python reais `text_core.run` e `media.review` ainda não são executados pela Edge Function Deno;
- publicação real continua bloqueada até aprovação + autorização explícita;
- Reviewer de mídia ainda não faz compreensão visual semântica quadro a quadro;
- alertas são visíveis no painel, mas ainda não são enviados externamente.

## Próximo passo
Etapa 10 recomendada: homologar handlers reais com atores sintéticos, criar uma fila de aprovação operável sem publicação automática e adicionar notificações de falha/espera para o administrador de teste.
