from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str = field(default_factory=lambda: _resolve_db_path())
    log_file: str = ""


def _resolve_db_path() -> str:
    """
    Cloud platformalarda /data papkasi mavjud bo'lsa (Railway volume),
    shu papkada saqlaydi. Aks holda joriy papkada.
    """
    env_path = os.getenv("DB_PATH", "").strip()
    if env_path:
        return env_path
    if os.path.isdir("/data"):
        return "/data/edubot.db"
    return "edubot.db"


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    admin_raw = os.getenv("ADMIN_ID", "").strip()
    db_path = _resolve_db_path()
    log_file = os.getenv("LOG_FILE", "").strip()

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in environment variables.")
    if not admin_raw:
        raise ValueError("ADMIN_ID is not set in environment variables.")
    if not admin_raw.isdigit():
        raise ValueError("ADMIN_ID must be numeric.")

    return Config(
        bot_token=bot_token,
        admin_id=int(admin_raw),
        db_path=db_path,
        log_file=log_file,
    )
