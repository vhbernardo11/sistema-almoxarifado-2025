# IntegraSquad

Repositório canônico do **IntegraSquad**, o motor multiagente da Integra.

## Estado atual

- ✅ Etapa 1 — consolidação no GitHub
- ✅ Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter
- ✅ Etapa 3 — memória e estado persistentes no Supabase
- ✅ Etapa 4 — aprovação humana + Publisher preparado
- ⏳ Etapa 5 — imagem/vídeo, somente depois da base textual e operacional

## Fluxo atual

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> memória/checkpoints -> aprovação humana -> Publisher preparado`

A aprovação humana é **fail-closed**: ela fica vinculada ao `run_id` e ao SHA-256 do payload aprovado. Se o conteúdo mudar depois da aprovação, o Publisher bloqueia novamente. Uma aprovação não pode ser reutilizada em outra execução.

O Publisher também exige uma segunda autorização explícita no momento de uma futura execução externa. Nesta etapa nenhum post foi criado, agendado ou publicado.

## Persistência

O projeto usa tabelas `squad_*` isoladas no Supabase para runs, tasks, artifacts, events, checkpoints, memories, approvals e publications. As tabelas do IntegraSquad têm RLS habilitado e não concedem acesso a `anon` ou `authenticated`; o acesso previsto é server-side.

## Metricool

A integração disponível foi inspecionada e o código contém um builder de payload compatível com o fluxo de publicação. A chamada externa permanece separada atrás do `ApprovalGate` e do `PublisherService`.

## Princípios

- agentes pensam e produzem; ferramentas executam ações externas;
- nenhuma publicação externa sem aprovação humana explícita;
- conteúdo alterado depois da aprovação precisa ser aprovado novamente;
- segredos nunca entram no Git;
- cada etapa precisa ser testável isoladamente;
- mídia não pode bloquear o núcleo do produto.

## Testes

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
```

## Documentação

- `docs/ETAPA2_TEXT_CORE.md`
- `docs/ETAPA3_MEMORY.md`
- `docs/ETAPA4_APPROVAL_PUBLISHER.md`
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/REBUILD_ROADMAP.md`
