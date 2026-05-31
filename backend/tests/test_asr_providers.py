from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import urllib.error

import pytest
from fastapi.testclient import TestClient

# Isolate DB/audio to a temp dir (mirrors test_recordings.py).
_TEST_ROOT = Path(tempfile.mkdtemp(prefix="game-voice-ai-asr-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_ROOT / 'recordings.sqlite3'}"
os.environ["AUDIO_STORAGE_DIR"] = str(_TEST_ROOT / "audio")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app import config, transcriptions
from app import asr_status as asr_status_module
from app.asr import (
    ASRProviderError,
    FunasrHttpASRProvider,
    get_asr_provider,
    parse_funasr_response,
)
from app.config import get_settings
from app.database import Base, engine
from app.main import app
from app.models import Recording


@pytest.fixture(autouse=True)
def clean_local_data() -> None:
    settings = get_settings()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    settings.audio_storage_dir.mkdir(parents=True, exist_ok=True)
    for path in settings.audio_storage_dir.iterdir():
        if path.name != ".gitkeep" and path.is_file():
            path.unlink()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _upload(client: TestClient) -> str:
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.wav", BytesIO(b"fake wav bytes"), "audio/wav")},
    )
    assert response.status_code == 201
    return response.json()["id"]


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = 200

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


# --- factory routing ---------------------------------------------------------


def test_provider_factory_resolves_all_three(monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import replace

    base = get_settings()
    assert type(get_asr_provider(replace(base, asr_provider="mock"))).__name__ == "MockASRProvider"
    assert type(get_asr_provider(replace(base, asr_provider="aliyun"))).__name__ == "AliyunASRProvider"
    assert (
        type(get_asr_provider(replace(base, asr_provider="funasr_http"))).__name__
        == "FunasrHttpASRProvider"
    )


def test_unknown_provider_returns_clear_error() -> None:
    from dataclasses import replace

    with pytest.raises(ASRProviderError) as excinfo:
        get_asr_provider(replace(get_settings(), asr_provider="whisper_x"))
    assert "funasr_http" in str(excinfo.value.detail)


# --- mock provider still works ----------------------------------------------


def test_mock_provider_still_transcribes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ASR_PROVIDER", "mock")
    recording_id = _upload(client)
    response = client.post(f"/api/recordings/{recording_id}/transcribe")
    assert response.status_code == 201
    payload = response.json()
    assert len(payload) >= 1
    assert payload[0]["source"] == "mock"


# --- funasr_http provider ----------------------------------------------------


def test_funasr_http_requests_configured_base_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ASR_PROVIDER", "funasr_http")
    monkeypatch.setenv("FUNASR_HTTP_BASE_URL", "http://10.0.0.7:10095")
    monkeypatch.setenv("FUNASR_HTTP_TRANSCRIBE_PATH", "/asr")

    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):  # noqa: ANN001
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return _FakeResponse(
            {
                "segments": [
                    {"text": "中路集合", "start": 0.0, "end": 2.0, "spk": 0},
                    {"text": "拿龙", "start": 2.0, "end": 4.0, "spk": 1},
                ]
            }
        )

    monkeypatch.setattr("app.asr.urllib.request.urlopen", fake_urlopen)

    recording_id = _upload(client)
    response = client.post(f"/api/recordings/{recording_id}/transcribe")

    assert response.status_code == 201, response.text
    assert captured["url"] == "http://10.0.0.7:10095/asr"
    assert captured["method"] == "POST"
    payload = response.json()
    assert [s["text"] for s in payload] == ["中路集合", "拿龙"]
    assert all(s["source"] == "funasr_http" for s in payload)


def test_funasr_http_unreachable_returns_clear_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ASR_PROVIDER", "funasr_http")
    monkeypatch.setenv("FUNASR_HTTP_BASE_URL", "http://127.0.0.1:10095")

    def boom(request, timeout):  # noqa: ANN001
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("app.asr.urllib.request.urlopen", boom)

    recording_id = _upload(client)
    response = client.post(f"/api/recordings/{recording_id}/transcribe")

    assert response.status_code == 503
    assert "FunASR 服务未连接" in response.json()["detail"]


def test_funasr_mock_response_converts_to_segments() -> None:
    class _Rec:
        duration = 9.0

    segments = parse_funasr_response(
        {"sentences": [{"value": "开团", "begin_time": 1500, "end_time": 4500}]},
        _Rec(),
    )
    assert len(segments) == 1
    assert segments[0].text == "开团"
    assert segments[0].start_time == 1.5
    assert segments[0].end_time == 4.5
    assert segments[0].source == "funasr_http"


@pytest.mark.parametrize(
    ("payload", "expected_texts"),
    [
        (
            {
                "text": "大家准备一下，我先去中路看视野",
                "segments": [
                    {"start": 0, "end": 3000, "text": "大家准备一下"},
                    {"start": 3000, "end": 7000, "text": "我先去中路看视野"},
                ],
            },
            ["大家准备一下", "我先去中路看视野"],
        ),
        (
            {
                "text": "句子信息",
                "sentence_info": [
                    {"start": 0, "end": 3000, "text": "句子信息"}
                ],
            },
            ["句子信息"],
        ),
        (
            {
                "result": {
                    "text": "嵌套结果",
                    "segments": [{"start": 0, "end": 3000, "text": "嵌套结果"}],
                }
            },
            ["嵌套结果"],
        ),
        (
            [
                {
                    "text": "列表包装",
                    "sentence_info": [
                        {"start": 0, "end": 3000, "text": "列表包装"}
                    ],
                }
            ],
            ["列表包装"],
        ),
    ],
)
def test_funasr_parser_accepts_common_response_shapes(
    payload: object, expected_texts: list[str]
) -> None:
    class _Rec:
        duration = 12.0

    segments = parse_funasr_response(payload, _Rec())
    assert [segment.text for segment in segments] == expected_texts
    assert segments[0].start_time == 0.0
    assert segments[0].end_time == 3.0
    assert all(segment.source == "funasr_http" for segment in segments)


def test_funasr_plain_text_response_spans_recording() -> None:
    class _Rec:
        duration = 7.0

    segments = parse_funasr_response({"text": "整段没有时间戳"}, _Rec())
    assert len(segments) == 1
    assert segments[0].start_time == 0.0
    assert segments[0].end_time == 7.0
    assert segments[0].text == "整段没有时间戳"


# --- AI summary still works after funasr transcription ----------------------


def test_summary_works_after_funasr_transcription(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ASR_PROVIDER", "funasr_http")
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    def fake_urlopen(request, timeout):  # noqa: ANN001
        return _FakeResponse(
            {"segments": [{"text": "推高地", "start": 0.0, "end": 3.0, "spk": 0}]}
        )

    monkeypatch.setattr("app.asr.urllib.request.urlopen", fake_urlopen)

    recording_id = _upload(client)
    assert client.post(f"/api/recordings/{recording_id}/transcribe").status_code == 201

    analyze = client.post(f"/api/recordings/{recording_id}/analyze")
    assert analyze.status_code in (200, 201), analyze.text
    body = analyze.json()
    assert body  # mock summary produced from the funasr segments


# --- status endpoint ---------------------------------------------------------


def test_asr_status_endpoint_reports_providers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ASR_PROVIDER", "funasr_http")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    # Avoid a real network probe in the status endpoint.
    monkeypatch.setattr(
        asr_status_module, "_probe_funasr", lambda base_url, timeout=2.0: (False, "stubbed")
    )

    response = client.get("/api/asr/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "funasr_http"
    assert data["asr_provider"] == "funasr_http"
    assert data["supported_providers"] == ["mock", "aliyun", "funasr_http"]
    assert data["aliyun"]["configured"] is True
    assert data["aliyun"]["api_key_configured"] is True
    assert data["aliyun"]["public_base_url_configured"] is True
    assert data["aliyun"]["public_url_is_local"] is True
    assert data["funasr_http"]["configured"] is True
    assert data["funasr_http"]["reachable"] is False
    assert data["funasr_http"]["error"] == "stubbed"
    assert data["funasr_http"]["base_url"].startswith("http")
