# IntegraSquad

Repositório canônico do **IntegraSquad**, o motor multiagente da Integra.

## Estado atual

- ✅ Etapa 1 — consolidação no GitHub
- ✅ Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter
- ✅ Etapa 3 — memória e estado persistentes no Supabase
- ✅ Etapa 4 — aprovação humana + Publisher preparado
- ✅ Etapa 5 — núcleo de mídia determinístico, sem depender de TTS
- ✅ Etapa 6 — Reviewer de mídia, templates e ponte de aprovação/publicação

## Fluxo atual

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> memória/checkpoints -> mídia -> QA -> aprovação humana -> Publisher preparado`

O QA de mídia verifica o artefato final por regras determinísticas: SHA-256, resolução, proporção 9:16, FPS, duração, codec e áudio quando exigido. O relatório não finge uma revisão visual semântica: seu escopo é `artifact_and_metadata`.

A aprovação humana é **fail-closed**: ela fica vinculada ao `run_id`, ao conteúdo, ao alvo de publicação e ao SHA-256 exato do vídeo. Se o vídeo, o texto, a conta, o horário ou o destino mudar depois da aprovação, o Publisher bloqueia novamente.

O Publisher ainda exige uma segunda autorização explícita no momento de uma futura execução externa. Nenhum post é criado, agendado ou publicado automaticamente por esta etapa.

## Persistência

O projeto usa tabelas `squad_*` isoladas no Supabase para runs, tasks, artifacts, events, checkpoints, memories, approvals e publications. As tabelas do IntegraSquad têm RLS habilitado e não concedem acesso a `anon` ou `authenticated`; o acesso previsto é server-side.

## Mídia

O pacote `src/integra/media` contém:
- `MediaManifest` e contratos de cena;
- `FFmpegMediaRenderer`;
- `review_media()` e `probe_video()`;
- três templates iniciais;
- ponte que cria payload de aprovação contendo o hash exato da mídia.

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
- `docs/ETAPA5_MEDIA.md`
- `docs/ETAPA6_REVIEW.md`
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/REBUILD_ROADMAP.md`
