from __future__ import annotations

import argparse

from .models import CampaignRequest
from .workflow import result_as_json, run_text_core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa o núcleo textual do IntegraSquad")
    parser.add_argument("--goal", required=True, help="Objetivo da campanha")
    parser.add_argument("--audience", help="Público-alvo")
    parser.add_argument("--location", help="Localidade")
    parser.add_argument("--channel", default="instagram", help="Canal principal")
    parser.add_argument("--tone", default="claro, humano e comercial", help="Tom da comunicação")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    request = CampaignRequest(
        goal=args.goal,
        audience=args.audience,
        location=args.location,
        channel=args.channel,
        tone=args.tone,
    )
    result = run_text_core(request)
    print(result_as_json(result))


if __name__ == "__main__":
    main()
