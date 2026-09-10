from __future__ import annotations

import argparse

from integra.memory import SupabaseMemoryStore

from .models import CampaignRequest
from .persistent import run_text_core_persistent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa o núcleo textual com estado persistente no Supabase."
    )
    parser.add_argument("--goal", required=True)
    parser.add_argument("--audience")
    parser.add_argument("--location")
    parser.add_argument("--channel", default="instagram")
    parser.add_argument("--tone", default="claro, humano e comercial")
    args = parser.parse_args()

    store = SupabaseMemoryStore.from_env()
    result = run_text_core_persistent(
        CampaignRequest(
            goal=args.goal,
            audience=args.audience,
            location=args.location,
            channel=args.channel,
            tone=args.tone,
        ),
        store=store,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
