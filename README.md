# IntegraSquad

Repositório canônico do projeto **IntegraSquad**, o motor multiagente da Integra para transformar objetivos em pesquisa, estratégia, copy, briefs, revisão, aprovação e — mais adiante — execução externa.

## Estado atual

**Etapa 1 — consolidação no GitHub: concluída.**  
**Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter: implementada e testada.**

Este repositório é a fonte de verdade do projeto. O código experimental das sessões anteriores não é tratado como produção; o histórico e as decisões reaproveitáveis estão documentados em `docs/`, e o projeto antigo reaproveitado permanece preservado na branch `archive/pre-integrasquad`.

## Ordem de construção

1. ✅ Consolidar tudo no GitHub.
2. ✅ Reconstruir o núcleo textual de forma limpa.
3. ⏳ Criar memória/estado no Supabase.
4. ⏳ Preparar aprovação humana + Publisher.
5. ⏳ Só depois voltar para imagem/vídeo.

## Núcleo textual v0.2

O fluxo implementado é:

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> TextCoreResult`

- Researcher: usa busca web pelo OpenAI Agents SDK e devolve pesquisa estruturada com fontes.
- Strategist: transforma pesquisa em posicionamento, mensagem, CTA e guardrails.
- Copywriter: gera o pacote de copy e o brief visual.
- Nenhum desses agentes publica ou agenda conteúdo.
- `publication_authorized` permanece `false` nesta etapa.

Consulte `docs/ETAPA2_TEXT_CORE.md` para o contrato detalhado.

## Instalação e testes

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
python -m integra.main
```

Os testes automatizados não consomem a OpenAI API. Para executar o núcleo textual live, disponibilize `OPENAI_API_KEY` em um ambiente seguro e rode:

```bash
python -m integra.text_core.cli \
  --goal "Criar campanha para apresentar o IntegraTrampo a eletricistas" \
  --audience "Eletricistas autônomos" \
  --location "Teodoro Sampaio, SP"
```

A chave nunca deve ser commitada no GitHub.

## Princípios

- agentes pensam e produzem; ferramentas executam ações externas;
- publicação externa exige aprovação humana explícita;
- segredos nunca entram no Git;
- cada etapa precisa ser testável isoladamente;
- mídia não pode bloquear o núcleo do produto;
- o repositório canônico deve permitir retomar o trabalho sem depender de uma sessão de chat.

## Documentos principais

- `docs/ARCHITECTURE.md` — arquitetura canônica.
- `docs/REBUILD_ROADMAP.md` — nova sequência de reconstrução.
- `docs/PROJECT_STATUS.md` — estado confirmado do projeto.
- `docs/PROTOTYPE_HISTORY.md` — histórico das Etapas 1–7 e lições aprendidas.
- `docs/ETAPA2_TEXT_CORE.md` — contrato e operação do núcleo textual.
- `archive/` — contexto preservado; a branch `archive/pre-integrasquad` mantém o sistema antigo reaproveitado.
