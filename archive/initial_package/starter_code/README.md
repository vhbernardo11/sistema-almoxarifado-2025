# IntegraSquad — Starter da Etapa 1

## Instalação

### macOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python -m integra.main
```

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q
python -m integra.main
```

A chave da OpenAI ainda não é necessária para o smoke test estrutural.
Quando a Etapa 2 começar, configure `OPENAI_API_KEY` em `.env` sem compartilhar ou commitar o valor.
