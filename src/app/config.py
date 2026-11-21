from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets remain environment-only."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="POCKETSRE_", extra="ignore")

    environment: str = "development"
    magic_link_secret: str = "development-only-change-me"
    discord_token: str | None = None
    discord_guild_id: int | None = None
    target_ssh_host: str | None = None
    target_ssh_user: str = "pocketsre"
    target_ssh_key_path: Path = Path("/app/.ssh/pocketsre_bot_ed25519")
    autonomy_mode: str = "strict_confirmation"
    web_dist_path: Path = Path("src/web/dist")
    gemini_api_keys: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"
    llm_request_timeout_seconds: float = 20.0
    llm_max_retries: int = 2

    @property
    def gemini_keys(self) -> list[str]:
        """Comma-separated environment input without exposing individual secrets in logs."""
        return [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
