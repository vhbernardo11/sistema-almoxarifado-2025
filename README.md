# IntegraSquad

Repositório canônico do projeto **IntegraSquad**, o motor multiagente da Integra para transformar objetivos em pesquisa, estratégia, copy, memória persistente, revisão, aprovação e — mais adiante — execução externa.

## Estado atual

**Etapa 1 — consolidação no GitHub: concluída.**  
**Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter: implementada e testada.**  
**Etapa 3 — memória/estado no Supabase: implementada, aplicada e testada.**

Este repositório é a fonte de verdade do projeto. O código experimental das sessões anteriores não é tratado como produção; o histórico e as decisões reaproveitáveis estão documentados em `docs/`, e o projeto antigo reaproveitado permanece preservado na branch `archive/pre-integrasquad`.

## Ordem de construção

1. ✅ Consolidar tudo no GitHub.
2. ✅ Reconstruir o núcleo textual de forma limpa.
3. ✅ Criar memória/estado no Supabase.
4. ⏳ Preparar aprovação humana + Publisher.
5. ⏳ Só depois voltar para imagem/vídeo.

## Núcleo textual persistente v0.3

O fluxo atual é:

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> TextCoreResult`

Quando executado por `run_text_core_persistent`, o mesmo fluxo também grava `Run -> Tasks -> Events -> Checkpoints -> ResumeState` no Supabase.

- Researcher: usa busca web pelo OpenAI Agents SDK e devolve pesquisa estruturada com fontes.
- Strategist: transforma pesquisa em posicionamento, mensagem, CTA e guardrails.
- Copywriter: gera o pacote de copy e o brief visual.
- Supabase registra estado, resultados, histórico e checkpoints.
- `squad_memories` armazena memória estruturada por escopo/chave.
- Nenhum desses agentes publica ou agenda conteúdo.
- `publication_authorized` permanece `false`.

Consulte `docs/ETAPA2_TEXT_CORE.md` e `docs/ETAPA3_MEMORY.md`.

## Instalação e testes

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
python -m integra.main
```

Os testes automatizados não consomem a OpenAI API nem exigem Supabase. Para executar o fluxo persistente live, instale os extras e configure os segredos somente no backend:

```bash
pip install -e ".[all]"
python -m integra.text_core.persistent_cli \
  --goal "Criar campanha para apresentar o IntegraTrampo a eletricistas" \
  --audience "Eletricistas autônomos" \
  --location "Teodoro Sampaio, SP"
```

São exigidos `OPENAI_API_KEY`, `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` no ambiente seguro. Nenhuma chave deve ser commitada no GitHub ou enviada ao frontend.

## Princípios

- agentes pensam e produzem; ferramentas executam ações externas;
- publicação externa exige aprovação humana explícita;
- segredos nunca entram no Git;
- cada etapa precisa ser testável isoladamente;
- mídia não pode bloquear o núcleo do produto;
- o repositório canônico e o Supabase devem permitir retomar o trabalho sem depender de uma sessão de chat.

## Documentos principais

- `docs/ARCHITECTURE.md` — arquitetura canônica.
- `docs/REBUILD_ROADMAP.md` — sequência de reconstrução.
- `docs/PROJECT_STATUS.md` — estado confirmado do projeto.
- `docs/PROTOTYPE_HISTORY.md` — histórico dos protótipos e lições aprendidas.
- `docs/ETAPA2_TEXT_CORE.md` — contrato do núcleo textual.
- `docs/ETAPA3_MEMORY.md` — contrato de persistência e segurança.
- `supabase/migrations/` — migrações aplicadas na infraestrutura.
- `archive/` — contexto preservado; a branch `archive/pre-integrasquad` mantém o sistema antigo reaproveitado.
