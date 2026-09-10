# Arquitetura canônica — IntegraSquad

## Núcleo

```text
Usuário
  |
  v
Maestro
  |
  +--> Pesquisador
  +--> Estrategista
  +--> Copywriter
  +--> Designer / Brief visual
  +--> Revisor
  |
  v
Checkpoint humano
  |
  v
Publisher
```

## Persistência

```text
Run -> Tasks -> AgentResults -> Artifacts -> Checkpoints
                          |
                       Supabase
```

## Regra central

**Agentes pensam e produzem. Ferramentas executam ações determinísticas ou externas.**

O Publisher tem efeito externo e só pode operar após aprovação humana explícita.

## Decisão de reconstrução

Imagem, vídeo e voz não fazem parte do caminho crítico da primeira versão reconstruída. Eles voltarão apenas depois de o núcleo textual, a persistência e a aprovação/publicação estarem estáveis.
