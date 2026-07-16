from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "flowy"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./flowy.db"

    google_api_key: str = ""
    mock_llm: bool = True

    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@flowy.local"


settings = Settings()
