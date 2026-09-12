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
- ✅ Etapa 12 — especialistas determinísticos operacionais
- ✅ Etapa 13 — especialistas conectados à fila, runtime hospedado e Sala de Controle

## Fluxo

`Pedido -> Maestro -> especialistas -> squad_jobs -> worker -> resultado/checkpoint -> revisão/aprovação humana -> Publisher separado`

A autonomia **não atravessa a barreira humana de publicação**.

## Etapa 13

Programmer, Tester, Commercial, Legal Reviewer, SEO Analyst e Analytics agora possuem tipos de job `specialist.*` e passam pela fila persistente. Um worker hospedado específico reclama somente esses jobs sintéticos, e a Sala de Controle mostra o status de cada especialista.

O runtime segue estritamente **test-only**: exige `test_mode=true`, atores `stage8-test-*`, `publication_authorized=false` e `external_actions_authorized=false`.

## Etapa 10

A execução agentic baseada em modelo permanece adiada. Nenhum job de IA ao vivo é necessário para os executores determinísticos das Etapas 12–13.

## Segurança

- aprovação humana fail-closed;
- Publisher não pertence às rotas automáticas;
- usuários reais ficam fora da homologação;
- segredos ficam fora do Git;
- nenhuma publicação externa é feita durante homologação;
- especialistas das Etapas 12–13 são determinísticos e test-only.

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
- `docs/PROJECT_STATUS.md`
