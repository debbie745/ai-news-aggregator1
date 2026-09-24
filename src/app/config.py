from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str

    groq_api_key: str | None = None

    gmail_credentials_path: str = "credentials/gmail_credentials.json"
    gmail_token_path: str = "credentials/gmail_token.json"
    # Off by default in a deployed/cron context (set via env var there) --
    # Gmail's OAuth token expires every ~7 days while this app stays in
    # Google's "Testing" publish status, and the browser-based re-consent
    # can't run unattended. Keep it True locally where you can re-auth by
    # hand; a scheduled deployment should set this to false.
    enable_gmail_ingestion: bool = True

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None

    digest_recipient_email: str | None = None
    digest_sender_email: str | None = None

    system_prompt_path: str = "src/app/prompts/user_insight_system_prompt.md"

    @property
    def effective_sender_email(self) -> str | None:
        return self.digest_sender_email or self.smtp_username


@lru_cache
def get_settings() -> Settings:
    return Settings()
