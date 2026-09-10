from __future__ import annotations

import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "IntegraSquad"
    environment: str = os.getenv("INTEGRA_ENV", "development")
    openai_api_key_present: bool = bool(os.getenv("OPENAI_API_KEY"))


settings = Settings()
