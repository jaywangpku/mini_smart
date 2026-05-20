from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps local SQLite helpers usable before dependency install.
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    db_path: Path
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    jwt_secret: str = "mini-smart-local-secret"
    token_expire_hours: int = 168


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    raw_db_path = os.getenv("MINI_SMART_DB_PATH", "data/market.sqlite")
    db_path = Path(raw_db_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    jwt_secret = os.getenv("MINI_SMART_JWT_SECRET", "mini-smart-local-secret")
    token_expire_hours = int(os.getenv("MINI_SMART_TOKEN_EXPIRE_HOURS", "168"))
    return Settings(db_path=db_path, jwt_secret=jwt_secret, token_expire_hours=token_expire_hours)


def ensure_data_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
