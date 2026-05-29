from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

from fastapi import APIRouter

from .config import get_settings

router = APIRouter(prefix="/api/asr", tags=["asr"])


def _public_url_is_local(public_base_url: str) -> bool:
    hostname = urllib.parse.urlparse(public_base_url).hostname
    return hostname in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _probe_funasr(base_url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """Best-effort reachability probe. Never raises.

    A FunASR HTTP service is considered "reachable" if the base URL answers at
    all (any HTTP status counts — even 404/405 means the host:port is up).
    """

    try:
        request = urllib.request.Request(base_url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return True, f"HTTP {response.status}"
    except urllib.error.HTTPError as error:
        # Host is up but the root path isn't a GET endpoint — still reachable.
        return True, f"HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return False, str(getattr(error, "reason", error))


@router.get("/status")
def asr_status() -> dict[str, object]:
    settings = get_settings()
    funasr_reachable, funasr_detail = _probe_funasr(settings.funasr_http_base_url)

    return {
        "asr_provider": settings.asr_provider,
        "supported_providers": ["mock", "aliyun", "funasr_http"],
        "aliyun": {
            "api_key_configured": bool(settings.dashscope_api_key),
            "model": settings.aliyun_asr_model,
            "public_base_url": settings.public_base_url,
            "public_url_is_local": _public_url_is_local(settings.public_base_url),
        },
        "funasr_http": {
            "base_url": settings.funasr_http_base_url,
            "transcribe_path": settings.funasr_http_transcribe_path,
            "reachable": funasr_reachable,
            "detail": funasr_detail,
        },
    }
