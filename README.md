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
- 🚧 Etapa 10 — runtime agentic real em homologação, somente usuários sintéticos

## Fluxo

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> memória/checkpoints -> mídia -> QA -> aprovação humana -> Publisher preparado`

A execução operacional usa `squad_jobs`, workers, retries e checkpoints. A autonomia **não atravessa a barreira humana de publicação**.

## Etapa 10

O runtime `integrasquad-stage10-runtime` está preparado para processar `text_core.run` apenas quando `test_mode=true` e o ator for `stage8-test-*`. O Researcher usa busca web; Strategist e Copywriter recebem os resultados estruturados. Ao final, o sistema cria uma aprovação `pending` ligada ao SHA-256 do payload exato e mantém `publication_authorized=false`.

A fila de aprovação aparece na Sala de Controle, mas é somente leitura. O Publisher não faz parte do registro automático.

**Importante:** a chave criada no fluxo seguro do ChatGPT não é copiada automaticamente para o Supabase. Enquanto o secret `OPENAI_API_KEY` não existir no Edge Runtime, a Etapa 10 permanece armada porém não reclama jobs; isso evita execução parcial.

## Usuários de homologação

Somente identidades sintéticas `stage8-test-*`, com e-mails `@example.invalid`, podem entrar no runtime de teste. Usuários reais são bloqueados.

## Segurança

- aprovação humana fail-closed;
- mudança de payload invalida aprovação anterior;
- Publisher exige aprovação + autorização explícita de execução;
- segredos ficam fora do Git;
- RLS permanece ativo nas tabelas `squad_*`;
- nenhuma publicação externa é feita durante homologação.

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
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
