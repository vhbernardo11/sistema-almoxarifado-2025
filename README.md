# IntegraSquad

Repositório canônico do **IntegraSquad**, o motor multiagente da Integra.

## Estado atual

- ✅ Etapa 1 — consolidação no GitHub
- ✅ Etapa 2 — núcleo textual Researcher -> Strategist -> Copywriter
- ✅ Etapa 3 — memória e estado persistentes no Supabase
- ✅ Etapa 4 — aprovação humana + Publisher preparado
- ✅ Etapa 5 — núcleo de mídia determinístico
- ✅ Etapa 6 — Reviewer de mídia, templates e ponte de aprovação
- ✅ Etapa 7 — fila, scheduler, retries, heartbeat e checkpoint recovery
- ✅ Etapa 8 — runtime hospedado test-only + cron + observabilidade
- ✅ Etapa 9 — Sala de Controle read-only
- ⏸️ Etapa 10 — runtime agentic real implementado, homologação ao vivo adiada por decisão do usuário
- ✅ Etapa 11 — Maestro determinístico + catálogo de especialistas
- ✅ Etapa 12 — primeira onda de especialistas determinísticos
- ✅ Etapa 13 — especialistas conectados à fila, runtime hospedado e Sala de Controle
- ✅ Etapa 14 — workflows multi-especialista do Maestro + segunda onda determinística
- ✅ Etapa 15 — workflows duráveis, checkpoint por especialista e retomada sem repetir etapas concluídas

## Fluxo atual

`Pedido -> Maestro -> maestro.workflow.v2 -> ledger de etapas -> worker durável -> revisão/aprovação humana -> Publisher separado`

A autonomia **não atravessa a barreira humana de publicação**.

## Etapa 15

A Etapa 15 adiciona persistência granular ao workflow do Maestro. Cada especialista concluído é gravado em `squad_workflow_steps`, enquanto `squad_workflows` mantém a posição atual, progresso, status e necessidade de revisão humana.

Se um worker cair depois do segundo especialista, a execução seguinte não começa de novo: ela reconstrói as saídas já concluídas e continua no próximo passo. O novo tipo de job é `maestro.workflow.v2`.

A homologação real interrompeu propositalmente um fluxo de software depois de Researcher + Programmer. O job ficou em `retry` com `current_step=2`; a segunda execução retomou diretamente em Tester + Reviewer e terminou com 4/4 etapas, todas com uma única tentativa.

## Segurança

- homologação somente com atores `stage8-test-*`;
- `test_mode=true` obrigatório;
- `publication_authorized=false` protegido também por CHECK no banco;
- `external_actions_authorized=false` protegido também por CHECK no banco;
- RLS nas tabelas de workflow e acesso direto de `anon`/`authenticated` revogado;
- Publisher continua fora das rotas automáticas;
- nenhuma publicação externa é feita durante homologação.

## Testes

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Dashboard

https://vhbernardo11.github.io/sistema-almoxarifado-2025/integrasquad-dashboard/

## Documentação

- `docs/ETAPA12_SPECIALISTS.md`
- `docs/ETAPA13_RUNTIME_SPECIALISTS.md`
- `docs/ETAPA14_MAESTRO_WORKFLOWS.md`
- `docs/ETAPA15_DURABLE_WORKFLOWS.md`
- `docs/PROJECT_STATUS.md`
