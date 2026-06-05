from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .paths import resolve_data_paths


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path | None
    database_url: str
    audio_storage_dir: Path
    exports_dir: Path
    logs_dir: Path
    config_dir: Path
    max_upload_bytes: int
    allowed_extensions: frozenset[str]
    allowed_mime_types: frozenset[str]
    asr_provider: str
    dashscope_api_key: str | None
    aliyun_asr_model: str
    aliyun_dashscope_base_url: str
    public_base_url: str
    aliyun_asr_poll_interval_seconds: float
    aliyun_asr_max_polls: int
    aliyun_asr_request_timeout_seconds: float
    funasr_http_base_url: str
    funasr_http_health_path: str
    funasr_http_transcribe_path: str
    funasr_http_model: str | None
    funasr_http_timeout_seconds: float
    llm_provider: str
    dashscope_llm_model: str
    dashscope_llm_base_url: str
    openai_api_key: str | None
    openai_llm_model: str
    openai_llm_base_url: str
    llm_request_timeout_seconds: float


def _normalize_path_env(value: str, default: str) -> str:
    path = (value or default).strip()
    return "/" + path.lstrip("/")


def _normalize_asr_provider(value: str) -> str:
    provider = value.strip().lower()
    if provider in {"funasr", "funasr-http"}:
        return "funasr_http"
    return provider


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    # Source-tree .env (dev). setdefault semantics: first writer wins, so these
    # take priority over the data-dir .env loaded below.
    load_env_file(project_root / ".env")
    load_env_file(project_root / "backend" / ".env")

    data_paths = resolve_data_paths(project_root)
    # Desktop/frozen fallback: when LUNARIS_DATA_DIR is set, also read .env from
    # the data dir. In a PyInstaller binary `__file__` points at the temp unpack
    # dir, so the source-tree .env above is unreachable and keys (e.g.
    # DASHSCOPE_API_KEY) would be missing. Users drop a .env into the data dir's
    # config/ (or its root) to supply credentials without rebuilding the binary.
    if data_paths.data_dir is not None:
        load_env_file(data_paths.config_dir / ".env")
        load_env_file(data_paths.data_dir / ".env")

    max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))

    return Settings(
        project_root=project_root,
        data_dir=data_paths.data_dir,
        database_url=data_paths.database_url,
        audio_storage_dir=data_paths.audio_storage_dir,
        exports_dir=data_paths.exports_dir,
        logs_dir=data_paths.logs_dir,
        config_dir=data_paths.config_dir,
        max_upload_bytes=max_upload_bytes,
        allowed_extensions=frozenset({".mp3", ".wav", ".m4a", ".webm"}),
        allowed_mime_types=frozenset(
            {
                "audio/mpeg",
                "audio/mp3",
                "audio/wav",
                "audio/wave",
                "audio/x-wav",
                "audio/mp4",
                "audio/x-m4a",
                "audio/m4a",
                "audio/webm",
            }
        ),
        asr_provider=_normalize_asr_provider(os.getenv("ASR_PROVIDER", "aliyun")),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY") or None,
        aliyun_asr_model=os.getenv("ALIYUN_ASR_MODEL", "fun-asr"),
        aliyun_dashscope_base_url=os.getenv(
            "ALIYUN_DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/api/v1",
        ).rstrip("/"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip(
            "/"
        ),
        aliyun_asr_poll_interval_seconds=float(
            os.getenv("ALIYUN_ASR_POLL_INTERVAL_SECONDS", "2")
        ),
        aliyun_asr_max_polls=int(os.getenv("ALIYUN_ASR_MAX_POLLS", "60")),
        aliyun_asr_request_timeout_seconds=float(
            os.getenv("ALIYUN_ASR_REQUEST_TIMEOUT_SECONDS", "30")
        ),
        funasr_http_base_url=os.getenv(
            "FUNASR_HTTP_BASE_URL", "http://127.0.0.1:10095"
        ).rstrip("/"),
        funasr_http_health_path=_normalize_path_env(
            os.getenv("FUNASR_HTTP_HEALTH_PATH", "/health"), "/health"
        ),
        funasr_http_transcribe_path=_normalize_path_env(
            os.getenv("FUNASR_HTTP_TRANSCRIBE_PATH", "/asr"), "/asr"
        ),
        funasr_http_model=os.getenv("FUNASR_HTTP_MODEL", "").strip() or None,
        funasr_http_timeout_seconds=float(
            os.getenv("FUNASR_HTTP_TIMEOUT_SECONDS", "120")
        ),
        llm_provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
        dashscope_llm_model=os.getenv("DASHSCOPE_LLM_MODEL", "qwen-plus"),
        dashscope_llm_base_url=os.getenv(
            "DASHSCOPE_LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).rstrip("/"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_llm_model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
        openai_llm_base_url=os.getenv(
            "OPENAI_LLM_BASE_URL",
            "https://api.openai.com/v1",
        ).rstrip("/"),
        llm_request_timeout_seconds=float(
            os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "60")
        ),
    )
