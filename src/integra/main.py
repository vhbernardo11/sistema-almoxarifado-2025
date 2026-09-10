from __future__ import annotations

from integra.config import settings
from integra.models import Run


def smoke_test() -> Run:
    return Run(id="smoke-001", goal="Validar a fundação consolidada do IntegraSquad")


def main() -> None:
    run = smoke_test()
    print(f"{settings.app_name} OK")
    print(f"environment={settings.environment}")
    print(f"openai_key_present={settings.openai_api_key_present}")
    print(run.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
