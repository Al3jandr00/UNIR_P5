from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def _load_simple_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


if load_dotenv is not None:
    load_dotenv(ENV_PATH)
else:
    _load_simple_dotenv(ENV_PATH)


def _build_db_url() -> str:
    """Construye la URL de conexión desde variables individuales o desde DB_URL directa."""
    direct = os.getenv("DB_URL", "")
    if direct:
        return direct
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "tasks")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    sslmode = os.getenv("DB_SSLMODE", "require")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}?sslmode={sslmode}"


@dataclass(frozen=True)
class Settings:
    # Base de datos
    db_url: str = field(default_factory=_build_db_url)

    # OpenAI directo
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_temperature: float = field(default_factory=lambda: float(os.getenv("OPENAI_TEMPERATURE", "0.7")))
    openai_max_tokens: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS", "350")))
    openai_top_p: float = field(default_factory=lambda: float(os.getenv("OPENAI_TOP_P", "1.0")))
    openai_system_prompt: str = field(default_factory=lambda: os.getenv(
        "OPENAI_SYSTEM_PROMPT",
        "Eres un asistente util, claro y preciso. Responde en espanol salvo que el usuario pida otro idioma.",
    ))

    # Azure OpenAI
    azure_openai_api_key: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY", ""))
    azure_openai_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    azure_openai_model: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_MODEL", ""))
    azure_openai_api_version: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))

    allow_local_fallback: bool = field(
        default_factory=lambda: os.getenv("AI_ALLOW_LOCAL_FALLBACK", "false").lower() == "true"
    )

    @property
    def has_openai_config(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)

    @property
    def has_azure_config(self) -> bool:
        return bool(
            self.azure_openai_api_key
            and self.azure_openai_endpoint
            and self.azure_openai_model
        )


settings = Settings()
