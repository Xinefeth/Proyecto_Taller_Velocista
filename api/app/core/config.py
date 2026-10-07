"""Configuración leída del entorno (o del archivo .env de la raíz en local)."""

from pathlib import Path

from pydantic import Field
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

    # En la nube (Render, Railway, etc.) la base llega en una sola variable DATABASE_URL.
    # Si está presente, tiene prioridad sobre las POSTGRES_* de abajo (uso local con Docker).
    database_url_externa: str | None = Field(default=None, validation_alias="DATABASE_URL")

    postgres_user: str = "apaec_app"
    postgres_password: str = "cambia-esta-clave"
    postgres_db: str = "apaec_lab"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    device_token_velocista: str = "dev-token-velocista"
    device_token_cronometro: str = "dev-token-cronometro"

    @staticmethod
    def _con_driver_psycopg(url: str) -> str:
        """Normaliza el esquema al driver psycopg 3 que usan el motor y Alembic.

        Render entrega `postgres://` o `postgresql://`; SQLAlchemy necesita
        `postgresql+psycopg://` para elegir psycopg 3 explícitamente.
        """
        for prefijo in ("postgresql+psycopg://", "postgresql+psycopg2://"):
            if url.startswith(prefijo):
                return url
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        return url

    @property
    def database_url(self) -> str:
        if self.database_url_externa:
            return self._con_driver_psycopg(self.database_url_externa)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
