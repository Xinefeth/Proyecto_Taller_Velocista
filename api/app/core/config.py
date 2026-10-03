"""Configuración leída desde el archivo .env de la raíz del repositorio."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPO = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=RAIZ_REPO / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "desarrollo"
    log_level: str = "INFO"
    secret_key: str = "cambia-esto"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    postgres_user: str = "apaec_app"
    postgres_password: str = "cambia-esta-clave"
    postgres_db: str = "apaec_lab"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    device_token_velocista: str = "dev-token-velocista"
    device_token_cronometro: str = "dev-token-cronometro"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
