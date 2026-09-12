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

## Fluxo

`Pedido -> Maestro -> workflow multi-especialista -> squad_jobs -> worker -> resultado -> revisão/aprovação humana -> Publisher separado`

A autonomia **não atravessa a barreira humana de publicação**.

## Etapa 14

A Etapa 14 adiciona executores determinísticos para **Researcher, Strategist, Copywriter e Reviewer**, completando a cobertura dos especialistas usados pelas rotas do Maestro sem depender do runtime agentic da Etapa 10.

O novo job `maestro.workflow` executa uma rota inteira em sequência. Cada passo recebe payload explícito e pode referenciar a saída de uma etapa anterior com `{ "$step": "programmer", "path": "data.workspace" }`. Isso permite, por exemplo, o Programmer criar um workspace virtual e o Tester validar exatamente esse resultado.

Rotas disponíveis:

- `campaign`: Researcher -> Strategist -> Copywriter -> Reviewer
- `software`: Researcher -> Programmer -> Tester -> Reviewer
- `commercial`: Researcher -> Commercial -> Copywriter -> Reviewer
- `legal`: Researcher -> Legal Reviewer -> Reviewer
- `seo`: Researcher -> SEO Analyst -> Copywriter -> Reviewer
- `analytics`: Analytics -> Strategist -> Reviewer
- `operations`: Strategist -> Reviewer

O Reviewer da Etapa 14 sempre encaminha o resultado para revisão humana. O workflow nunca autoriza publicação nem efeitos externos.

## Segurança

- homologação somente com atores `stage8-test-*`;
- `test_mode=true` obrigatório;
- `publication_authorized=false` obrigatório;
- `external_actions_authorized=false` obrigatório;
- Publisher continua fora das rotas automáticas;
- Researcher determinístico não navega na web e apenas organiza material fornecido;
- Programmer continua restrito a workspace virtual;
- Legal Reviewer continua sendo triagem e exige humano;
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
- `docs/PROJECT_STATUS.md`
