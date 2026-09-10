# Arquitetura proposta — IntegraSquad

```text
Usuário
  |
  v
Maestro
  |
  +--> Pesquisador
  +--> Estrategista
  +--> Copywriter
  +--> Designer
  +--> Videomaker
  +--> Revisor
  |
  v
Checkpoint humano
  |
  v
Publisher
```

Camada transversal:

```text
Estado / memória / artefatos / logs / checkpoints
                |
             Supabase
```

## Regra central
Agentes pensam e produzem. Ferramentas executam ações determinísticas ou externas.
O Publisher é uma ferramenta/agente com efeito externo e exige aprovação humana.

## Modelo de execução futuro
Cada campanha é uma `Run`.
Cada Run contém `Tasks`.
Cada Task gera um `AgentResult` e zero ou mais `Artifacts`.
Quando uma tarefa termina, cria-se um checkpoint.
Se houver falha, a Run pode ser retomada do último checkpoint válido.

## Primeira prova de valor
Entrada:
> Crie uma campanha do IntegraTrampo para captar eletricistas.

Saída inicial (Etapa 3):
- pesquisa
- estratégia
- roteiro
- legenda
- CTA

Saída completa futura:
- tudo acima
- artes 9:16
- vídeo MP4
- relatório de revisão
- aprovação
- agendamento/publicação
