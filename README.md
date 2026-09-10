# IntegraSquad

Repositório canônico do projeto **IntegraSquad**, o motor multiagente da Integra para transformar objetivos em pesquisa, estratégia, copy, briefs, revisão, aprovação e — mais adiante — execução externa.

## Estado atual

**Etapa 1 da reconstrução: consolidação e fundação — concluída localmente.**

Este repositório é a nova fonte de verdade. O código experimental das sessões anteriores não é tratado como produção; o histórico e as decisões reaproveitáveis estão documentados em `docs/` e o pacote inicial foi preservado em `archive/`.

## Nova ordem de construção

1. Consolidar tudo no GitHub.
2. Reconstruir o núcleo textual de forma limpa.
3. Criar memória/estado no Supabase.
4. Preparar aprovação humana + Publisher.
5. Só depois voltar para imagem/vídeo.

## Princípios

- agentes pensam e produzem; ferramentas executam ações externas;
- publicação externa exige aprovação humana explícita;
- segredos nunca entram no Git;
- cada etapa precisa ser testável isoladamente;
- mídia não pode bloquear o núcleo do produto;
- o repositório canônico deve permitir retomar o trabalho sem depender de uma sessão de chat.

## Smoke test

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q
python -m integra.main
```

O smoke test da fundação **não precisa** de chave da OpenAI. O Agents SDK será ativado na Etapa 2.

## Documentos principais

- `docs/ARCHITECTURE.md` — arquitetura canônica.
- `docs/REBUILD_ROADMAP.md` — nova sequência de reconstrução.
- `docs/PROJECT_STATUS.md` — o que está confirmado, experimental e pendente.
- `docs/PROTOTYPE_HISTORY.md` — histórico das Etapas 1–7 e lições aprendidas.
- `archive/` — histórico textual, pacote inicial e contexto preservados no próprio GitHub; a branch `archive/pre-integrasquad` mantém o projeto antigo que foi reaproveitado.
