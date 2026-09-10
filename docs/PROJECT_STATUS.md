# Status do projeto — 2026-09-10

## Fonte de verdade
Este repositório é o ponto canônico a partir da reconstrução.

## Concluído e canônico
- Etapa 1: consolidação no GitHub;
- contexto e arquitetura originais preservados;
- contratos-base `Run`, `Task`, `AgentResult` e `Artifact`;
- regra de aprovação humana antes de publicação;
- núcleo textual estruturado `Researcher -> Strategist -> Copywriter`;
- Researcher com `WebSearchTool` do OpenAI Agents SDK;
- outputs tipados para pesquisa, estratégia e copy;
- CLI para execução live do núcleo textual;
- testes automatizados sem consumo de API;
- falha fechada quando `OPENAI_API_KEY` não está disponível;
- `publication_authorized=false` em toda a Etapa 2.

## Credenciais
Uma chave de projeto da OpenAI foi criada pelo fluxo seguro. O valor secreto não é armazenado no repositório. Para uma execução live, a chave precisa ser disponibilizada ao ambiente de execução como `OPENAI_API_KEY`.

## Experimental, não canônico
Nas sessões anteriores foram prototipados Maestro, Designer, Videomaker, Revisor e checkpoint humano, além de renders locais de PNG/MP4 e tentativas de voz. Esses experimentos continuam úteis como aprendizado, mas não são considerados produção.

## Ainda pendente
- validar uma execução live do núcleo textual em um ambiente que receba a chave com segurança;
- memória persistente no Supabase;
- aprovação humana canônica e Publisher;
- pipeline de mídia premium e confiável;
- dashboard;
- recuperação automática de falhas.

## Próxima etapa
Etapa 3 da reconstrução: criar memória e estado persistentes no Supabase, depois de confirmar a estabilidade do núcleo textual.
