# Arquitetura canônica — IntegraSquad

## Núcleo

```text
Usuário
  |
  v
Maestro
  |
  +--> Researcher
  +--> Strategist
  +--> Copywriter
  +--> Reviewer
  +--> Programmer* / Tester*
  +--> Commercial* / Legal Reviewer*
  +--> SEO Analyst* / Analytics*
  |
  v
Checkpoint humano
  |
  v
Publisher separado
```

`*` capacidade preparada: contrato definido, executor especializado ainda não conectado.

## Persistência

```text
Run -> Tasks -> AgentResults -> Artifacts -> Checkpoints
                          |
                       Supabase
```

## Regra central

**Agentes pensam e produzem. Ferramentas executam ações determinísticas ou externas.**

O Maestro planeja e roteia. Ele não publica, não envia mensagens e não transforma um pedido por efeito externo em autorização.

O Publisher tem efeito externo e só pode operar em fluxo separado após aprovação humana explícita e autorização de execução.

## Estados de capacidade

- `implemented`: componente existente e coberto por contrato/testes;
- `prepared`: papel e contrato definidos, mas executor ainda não conectado;
- `blocked`: indisponível deliberadamente.

Um plano que dependa de capacidade ainda não implementada deve declarar `ready_for_execution=false` em vez de fingir completude.

## Homologação da Etapa 10

O runtime agentic hospedado existe, mas sua homologação ao vivo foi adiada porque o secret `OPENAI_API_KEY` ainda não está no Edge Runtime. Essa pendência não autoriza atalhos nem efeitos externos.
