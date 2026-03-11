from __future__ import annotations

import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    pylon_api_key: str = ""
    pylon_api_base_url: str = "https://api.usepylon.com"

    slack_bot_token: str = ""

    anthropic_api_key: str = ""

    database_url: str = "sqlite+aiosqlite:///./mappings.db"


settings = Settings()


def load_customers() -> list[dict]:
    customers_path = Path(__file__).parent.parent / "config" / "customers.yaml"
    if not customers_path.exists():
        return []
    with open(customers_path) as f:
        data = yaml.safe_load(f)
    return data.get("customers", [])
