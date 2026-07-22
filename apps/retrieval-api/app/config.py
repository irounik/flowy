from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

# Load env before Cognee reads access-control flags at import time.
load_dotenv(REPO_ROOT / ".env")
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "flowy-retrieval-api"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    llm_api_key: str = ""
    default_dataset: str = "main_dataset"
    upload_dir: str = "data/uploads"
    cors_origins: str = "*"
    enable_backend_access_control: bool = False

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
