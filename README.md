# IntegraSquad

Repositório canônico do **IntegraSquad**, o motor multiagente da Integra.

## Estado atual

- ✅ Etapa 1 — consolidação no GitHub
- ✅ Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter
- ✅ Etapa 3 — memória e estado persistentes no Supabase
- ✅ Etapa 4 — aprovação humana + Publisher preparado
- ✅ Etapa 5 — núcleo de mídia determinístico
- ✅ Etapa 6 — Reviewer de mídia, templates e ponte de aprovação
- ✅ Etapa 7 — fila, scheduler, retries, heartbeat e checkpoint recovery
- ✅ Etapa 8 — runtime hospedado test-only + cron + observabilidade
- ✅ Etapa 9 — Sala de Controle read-only
- ⏸️ Etapa 10 — runtime agentic real implementado, homologação ao vivo adiada por decisão do usuário
- 🚧 Etapa 11 — Maestro determinístico + catálogo de especialistas e roteamento por tipo de trabalho

## Fluxo

`Pedido -> Maestro -> especialistas adequados -> memória/checkpoints -> QA -> aprovação humana -> Publisher separado`

A execução operacional usa `squad_jobs`, workers, retries e checkpoints. A autonomia **não atravessa a barreira humana de publicação**.

## Etapa 10

O runtime `integrasquad-stage10-runtime` está preparado para processar `text_core.run` apenas quando `test_mode=true` e o ator for `stage8-test-*`. O Researcher usa busca web; Strategist e Copywriter recebem os resultados estruturados. Ao final, o sistema cria uma aprovação `pending` ligada ao SHA-256 do payload exato e mantém `publication_authorized=false`.

A homologação ao vivo foi deliberadamente adiada. Enquanto o secret `OPENAI_API_KEY` não existir no Edge Runtime, o runtime não reclama jobs.

## Etapa 11

O pacote `integra.maestro` cria planos estruturados e reproduzíveis para rotas de campanha, software, comercial, jurídico, SEO, analytics e operações. Cada especialista possui estado explícito (`implemented`, `prepared` ou `blocked`).

O Maestro não finge que uma capacidade está pronta: se a rota depender de um especialista ainda apenas preparado, o plano retorna `ready_for_execution=false` e informa os bloqueios.

O Publisher existe no catálogo arquitetural, mas **não pertence a nenhuma rota automática**. Todo plano nasce com `publication_authorized=false` e `external_actions_authorized=false`.

## Usuários de homologação

Somente identidades sintéticas `stage8-test-*`, com e-mails `@example.invalid`, podem entrar no runtime de teste. Usuários reais são bloqueados.

## Segurança

- aprovação humana fail-closed;
- mudança de payload invalida aprovação anterior;
- Publisher exige aprovação + autorização explícita de execução;
- segredos ficam fora do Git;
- RLS permanece ativo nas tabelas `squad_*`;
- nenhuma publicação externa é feita durante homologação;
- o Maestro da Etapa 11 apenas planeja e não executa efeitos externos.

## Testes

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

## Dashboard

https://vhbernardo11.github.io/sistema-almoxarifado-2025/integrasquad-dashboard/

## Documentação

- `docs/ETAPA2_TEXT_CORE.md`
- `docs/ETAPA3_MEMORY.md`
- `docs/ETAPA4_APPROVAL_PUBLISHER.md`
- `docs/ETAPA5_MEDIA.md`
- `docs/ETAPA6_REVIEW.md`
- `docs/ETAPA7_AUTONOMY.md`
- `docs/ETAPA8_RUNTIME.md`
- `docs/ETAPA9_DASHBOARD.md`
- `docs/ETAPA10_LIVE_TEST_RUNTIME.md`
- `docs/ETAPA11_MAESTRO_SPECIALISTS.md`
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
