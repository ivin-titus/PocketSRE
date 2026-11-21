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
    ssh_connect_timeout_seconds: float = 10.0
    ssh_command_timeout_seconds: float = 30.0
    autonomy_mode: str = "strict_confirmation"
    role_permissions: str = "SRE-Lead:lead,DevOps:responder,Junior-Dev:viewer"
    public_base_url: str = "http://localhost:8080"
    web_dist_path: Path = Path("src/web/dist")
    gemini_api_keys: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"
    ai_provider: str = "gemini"  # gemini | openai
    openai_api_key: str = ""
    openai_base_url: str = ""  # OpenAI-compatible endpoints (e.g. OpenRouter)
    openai_model: str = "gpt-4o-mini"
    llm_request_timeout_seconds: float = 20.0
    llm_max_retries: int = 2
    presence_base_url: str = "https://yuki-net.ivin.site/presence"
    presence_endpoints: str = "central,discord,horiz,telegram"
    discord_infra_webhook: str = (
        "https://discord.com/api/webhooks/1516923595903864963/03DE8KxXouAORIWNIxe6zHtGuVEGka6HV4nVpwKebVLJNuFBRFOzZaLD8VHwARO_JLk0"
    )
    discord_alert_channel_id: int | None = None
    infra_docs_path: Path = Path("docs/infra")

    # Speech providers (Phase 2 — metered credits)
    sarvam_api_key: str | None = None
    smallest_ai_api_key: str | None = None

    # Persistence & integrations
    neon_database_url: str | None = None
    devin_api_key: str | None = None
    linear_api_key: str | None = None
    linear_team_id: str | None = None
    github_pat: str | None = None
    github_repo: str | None = None  # owner/repo for code-level issue tracking

    # Budget governor (USD caps; Gemini free tier counts $0)
    budget_per_incident_usd: float = 5.00
    budget_devin_usd: float | None = None
    budget_llm_usd: float | None = None
    budget_sarvam_usd: float | None = None
    budget_smallest_usd: float | None = None
    devin_session_cost_estimate_usd: float = 1.00
    llm_call_cost_estimate_usd: float = 0.00  # Gemini free tier; set small for OpenAI
    # Daily spend caps (UTC day); flat caps above are cumulative lifetime caps
    budget_devin_daily_usd: float | None = None
    budget_llm_daily_usd: float | None = None
    budget_sarvam_daily_usd: float | None = None
    budget_smallest_daily_usd: float | None = None
    max_trials_per_incident: int = 3
    execution_privilege_mode: str = "non_root"  # non_root | full_root (PRD §3)
    pr_watch_interval_seconds: float = 300.0  # poll cadence for Devin PR follow-ups
    pr_watch_timeout_minutes: float = 720.0  # stale-PR re-ping threshold
    # Alert-vs-noise decision layer
    decision_provider: str = "gemini_decision"  # gemini_decision | local | keywords
    decision_model: str = "gemini-decision-1"
    decision_base_url: str | None = None  # local decision model endpoint (Laya/Ollama-class)


    @property
    def gemini_keys(self) -> list[str]:
        """Comma-separated environment input without exposing individual secrets in logs."""
        return [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
