"""Central configuration. Everything is overridable with ``TONE_NEURON_*`` env vars."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


class Settings(BaseSettings):
    """Runtime settings.

    Defaults are safe and offline: no network, no API keys, no persistence of content.
    """

    model_config = SettingsConfigDict(
        env_prefix="TONE_NEURON_",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- identity -----------------------------------------------------------
    app_name: str = "Tone Neuron"
    version: str = "0.1.0"
    owner_name: str = "there"
    home_region: str = "US"
    target_language: str = "en"

    # --- knowledge layer ----------------------------------------------------
    okf_dir: Path = PACKAGE_ROOT / "data" / "knowledge"
    cards_file: Path = PACKAGE_ROOT / "data" / "cards.json"
    characters_file: Path = PACKAGE_ROOT / "data" / "characters.json"
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"
    embedder: str = "auto"  # auto | hashing | tfidf | st
    vector_store: str = "auto"  # auto | numpy | faiss | qdrant
    reranker: str = "auto"  # auto | lexical | cross-encoder | none
    sentence_transformer_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_dim: int = 768
    mmr_lambda: float = 0.65
    top_k: int = 5
    candidate_k: int = 24
    max_confidence: float = 0.95

    # --- ML -----------------------------------------------------------------
    region_model_file: str = "region_inference.joblib"
    risk_model_file: str = "risk_classifier.joblib"
    calorie_model_file: str = "noop"  # reserved

    # --- LLM rewrites (optional) -------------------------------------------
    enable_llm: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 20.0

    # --- privacy / session --------------------------------------------------
    max_events: int = 200
    session_ttl_hours: int = 24

    # --- Gmail --------------------------------------------------------------
    gmail_credentials_file: Path = Field(
        default_factory=lambda: Path.home() / ".tone-neuron" / "credentials.json"
    )
    gmail_token_file: Path = Field(
        default_factory=lambda: Path.home() / ".tone-neuron" / "token.json"
    )
    gmail_user_id: str = "me"
    gmail_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"

    # --- API ----------------------------------------------------------------
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"

    @property
    def index_dir(self) -> Path:
        return self.artifacts_dir / "knowledge_index"

    @property
    def model_dir(self) -> Path:
        return self.artifacts_dir / "models"

    @property
    def dataset_dir(self) -> Path:
        return self.artifacts_dir / "datasets"

    @property
    def mascot_assets_dir(self) -> Path:
        return self.artifacts_dir / "mascot"

    @property
    def state_dir(self) -> Path:
        return self.artifacts_dir / "state"

    @property
    def llm_ready(self) -> bool:
        return bool(self.enable_llm and self.llm_api_key)

    def ensure_dirs(self) -> None:
        for path in (
            self.artifacts_dir,
            self.index_dir,
            self.model_dir,
            self.dataset_dir,
            self.mascot_assets_dir,
            self.state_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
