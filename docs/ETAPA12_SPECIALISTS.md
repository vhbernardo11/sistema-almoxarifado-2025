# Etapa 12 — Especialistas determinísticos operacionais

A Etapa 12 transforma seis capacidades que estavam apenas `prepared` em executores determinísticos reais, sem depender da homologação ao vivo da Etapa 10.

## Princípio

O objetivo desta etapa não é fingir uma IA generativa sem credencial. Em vez disso, cada especialista recebeu uma função reproduzível que trabalha somente com dados fornecidos e permanece fail-closed para efeitos externos.

## Especialistas implementados

### Programmer
Opera somente sobre um **workspace virtual em memória**. Aceita operações declarativas `write_file`, `append_text`, `replace_text` e `delete_file`. Não grava no GitHub, disco, deploy ou produção.

### Tester
Valida o workspace virtual sem executar código arbitrário. Suporta:
- presença/ausência de arquivo;
- `contains` / `not_contains`;
- JSON válido;
- sintaxe Python via `ast.parse`.

### Commercial
Monta proposta de valor e roteiro de abordagem usando exclusivamente oferta, público, benefícios, provas e CTA fornecidos. Se não houver prova, o resultado avisa e não inventa números, depoimentos ou resultados.

### Legal Reviewer
Faz triagem por padrões de risco como exclusividade, multa, renovação automática, foro, dados pessoais/LGPD, garantias amplas e irrevogabilidade. Sempre exige revisão humana e não substitui advogado.

### SEO Analyst
Gera slug, title, meta description, H1 e outline a partir de tópico e palavras-chave fornecidos. Não inventa volume de busca, posição, concorrência ou dados externos.

### Analytics
Calcula deltas entre períodos, taxas de funil e alertas de queda a partir de métricas numéricas fornecidas. Não consulta nem modifica fontes externas.

## Segurança de homologação

`execute_specialist` exige simultaneamente:
- `test_mode=true`;
- `actor_id` começando por `stage8-test-`;
- `publication_authorized=false`;
- `external_actions_authorized=false`.

Qualquer violação bloqueia a execução.

## Integração com o Maestro

Os seis especialistas agora passam de `prepared` para `implemented`. Isso remove os bloqueios estruturais das rotas software, comercial, jurídico, SEO e analytics.

`Publisher` continua fora de todas as rotas automáticas.

## Limitações deliberadas

- Programmer não transforma linguagem natural em código; ele aplica mudanças declarativas seguras em workspace virtual.
- Tester não executa shell, processos nem código arbitrário.
- Commercial não envia mensagens.
- Legal Reviewer não fornece parecer jurídico final.
- SEO não consulta SERP ou ferramentas externas.
- Analytics não lê bancos, planilhas ou APIs sozinho.

Essas limitações são intencionais: a Etapa 12 cria executores reais e seguros sem reabrir a dependência de segredo da Etapa 10.
