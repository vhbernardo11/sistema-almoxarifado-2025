# Etapa 2 — Núcleo textual

Status: **implementada e coberta por testes automatizados**.

## Objetivo

Reconstruir o núcleo textual do IntegraSquad de forma simples e verificável, separando raciocínio dos agentes de qualquer ação externa.

Fluxo canônico:

`CampaignRequest -> Researcher -> Strategist -> Copywriter -> TextCoreResult`

Nenhum componente desta etapa publica, agenda, envia mensagens ou autoriza publicação.

## Agentes

### Researcher

Usa `WebSearchTool` do OpenAI Agents SDK e devolve `ResearchBrief` estruturado. Deve registrar fontes reais, evitar invenções e reduzir o nível de confiança quando a evidência for fraca.

### Strategist

Recebe o pedido original e o `ResearchBrief`. Converte a pesquisa em posicionamento, mensagem central, promessa, objeções, CTA e guardrails. Não possui ferramenta externa.

### Copywriter

Recebe pedido, pesquisa e estratégia. Entrega headline, copy principal, legendas, CTA, hashtags, claims utilizados e brief visual. Não possui ferramenta externa.

## Segurança e separação de responsabilidades

- somente o Researcher possui busca web nesta etapa;
- Strategist e Copywriter trabalham sobre dados estruturados recebidos;
- `publication_authorized` é sempre `false` no resultado desta etapa;
- a chave da OpenAI é lida apenas da variável `OPENAI_API_KEY` em tempo de execução e nunca é salva no Git;
- se a chave não estiver disponível, a execução live falha fechada antes de chamar o modelo.

## Execução live

Com a chave disponível no ambiente:

```bash
python -m integra.text_core.cli \
  --goal "Criar campanha para apresentar o IntegraTrampo a eletricistas" \
  --audience "Eletricistas autônomos" \
  --location "Teodoro Sampaio, SP"
```

A saída é um JSON estruturado com `research`, `strategy` e `copy`.

## Testes

Os testes não consomem API: injetam um runner falso para validar a cadeia completa, a passagem de contexto entre os três agentes, os outputs tipados e a trava de publicação. Há também um teste garantindo que o modo live falha sem `OPENAI_API_KEY`.

A validação live com um modelo real depende de disponibilizar a chave criada em um ambiente de execução seguro; a chave não é e não deve ser commitada no repositório.
