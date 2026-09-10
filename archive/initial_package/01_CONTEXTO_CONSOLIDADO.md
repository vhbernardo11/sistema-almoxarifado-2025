# Contexto consolidado da investigação

A conversa começou a partir da análise de uma oferta chamada “Squad100 — Seu Time de Agentes Autônomo”, apresentada como uma equipe de IA capaz de pesquisar, decidir, executar e entregar.

A investigação concluiu que a ideia central é tecnicamente reproduzível usando componentes públicos e integrações disponíveis:
- orquestração multiagente;
- handoffs/delegação;
- agentes especializados;
- geração de arte e vídeo;
- checkpoints e recuperação;
- publicação em redes sociais;
- memória/estado persistente;
- painel visual posterior.

A decisão proposta foi NÃO começar construindo dezenas de agentes nem um dashboard bonito.
O caminho recomendado é provar primeiro o motor.

Primeiro núcleo:
1. Maestro
2. Pesquisador
3. Estrategista
4. Copywriter

Depois:
5. Designer
6. Videomaker
7. Revisor
8. Publisher

A primeira meta prática é:
> O usuário pede uma campanha do IntegraTrampo para uma profissão; o sistema pesquisa, define estratégia, escreve o roteiro e, progressivamente, gera arte, vídeo e prepara publicação.

Princípio de segurança/qualidade:
> Publicação externa só acontece depois de aprovação humana explícita.
