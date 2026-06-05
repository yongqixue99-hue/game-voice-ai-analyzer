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


def _public_url_is_configured(public_base_url: str) -> bool:
    parsed = urllib.parse.urlparse(public_base_url)
    return bool(parsed.scheme and parsed.netloc)


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _probe_funasr(
    base_url: str, health_path: str = "/health", timeout: float = 2.0
) -> tuple[bool, str]:
    """Best-effort reachability probe. Never raises.

    A FunASR HTTP service is considered "reachable" if the base URL answers at
    all (any HTTP status counts — even 404/405 means the host:port is up).
    """

    if not base_url:
        return False, "FUNASR_HTTP_BASE_URL 未配置"

    probe_urls = (_join_url(base_url, health_path), base_url)
    last_error = ""
    for url in probe_urls:
        reachable, detail = _probe_url(url, timeout)
        if reachable:
            return True, detail
        last_error = detail

    return False, last_error


def _probe_url(url: str, timeout: float) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return True, f"{url} -> HTTP {response.status}"
    except urllib.error.HTTPError as error:
        # Host is up but the root path isn't a GET endpoint — still reachable.
        return True, f"{url} -> HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return False, str(getattr(error, "reason", error))


@router.get("/status")
def asr_status() -> dict[str, object]:
    settings = get_settings()
    funasr_reachable, funasr_detail = _probe_funasr(
        settings.funasr_http_base_url,
        settings.funasr_http_health_path,
    )
    public_base_url_configured = _public_url_is_configured(settings.public_base_url)
    public_url_is_local = _public_url_is_local(settings.public_base_url)
    aliyun_configured = bool(settings.dashscope_api_key)
    funasr_configured = bool(settings.funasr_http_base_url)

    return {
        "provider": settings.asr_provider,
        "asr_provider": settings.asr_provider,
        "supported_providers": ["mock", "aliyun", "funasr_http"],
        "aliyun": {
            "configured": aliyun_configured,
            "api_key_configured": bool(settings.dashscope_api_key),
            "model": settings.aliyun_asr_model,
            "public_base_url": settings.public_base_url,
            "public_base_url_configured": public_base_url_configured,
            "public_url_is_local": public_url_is_local,
        },
        "funasr_http": {
            "configured": funasr_configured,
            "base_url": settings.funasr_http_base_url,
            "health_path": settings.funasr_http_health_path,
            "transcribe_path": settings.funasr_http_transcribe_path,
            "model": settings.funasr_http_model,
            "reachable": funasr_reachable,
            "error": "" if funasr_reachable else funasr_detail,
            "detail": funasr_detail,
        },
    }
