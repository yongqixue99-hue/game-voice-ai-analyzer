from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import urllib.error

import pytest
from fastapi.testclient import TestClient

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="game-voice-ai-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_ROOT / 'recordings.sqlite3'}"
os.environ["AUDIO_STORAGE_DIR"] = str(_TEST_ROOT / "audio")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app import config, llm, transcriptions
from app.asr import ASRSegment, parse_aliyun_transcription_json
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import RecordingAnalysis


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


def test_health_endpoints_return_service_metadata(client: TestClient) -> None:
    for path in ("/health", "/api/health"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "service": "fastapi",
            "version": "0.1.0",
        }


def create_test_session(client: TestClient, title: str = "测试长录音") -> dict:
    response = client.post(
        "/api/recording-sessions",
        json={"title": title, "chunk_duration_seconds": 30},
    )
    assert response.status_code == 201
    return response.json()


def upload_test_session_chunk(
    client: TestClient,
    session_id: str,
    chunk_index: int,
    start_offset_seconds: float,
    end_offset_seconds: float,
) -> dict:
    response = client.post(
        f"/api/recording-sessions/{session_id}/chunks",
        data={
            "chunk_index": str(chunk_index),
            "start_offset_seconds": str(start_offset_seconds),
            "end_offset_seconds": str(end_offset_seconds),
        },
        files={
            "file": (
                f"session-{session_id}-chunk-{chunk_index}.webm",
                BytesIO(b"fake chunk bytes"),
                "audio/webm",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def test_upload_recording_creates_metadata_and_audio_file(client: TestClient) -> None:
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("match.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "match.mp3"
    assert payload["mime_type"] == "audio/mpeg"
    assert payload["status"] == "uploaded"
    assert payload["filename"].endswith(".mp3")
    assert (get_settings().project_root / payload["file_path"]).exists()


def test_upload_webm_recording_creates_metadata_and_audio_file(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/recordings/upload",
        files={
            "file": (
                "browser-recording-20260527-203000.webm",
                BytesIO(b"fake webm bytes"),
                "audio/webm",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "browser-recording-20260527-203000.webm"
    assert payload["mime_type"] == "audio/webm"
    assert payload["status"] == "uploaded"
    assert payload["filename"].endswith(".webm")
    assert (get_settings().project_root / payload["file_path"]).exists()


def test_upload_webm_recording_accepts_codec_content_type(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/recordings/upload",
        files={
            "file": (
                "browser-recording-20260527-203001.webm",
                BytesIO(b"fake webm bytes"),
                "audio/webm;codecs=opus",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["mime_type"] == "audio/webm"
    assert payload["filename"].endswith(".webm")


def test_create_recording_session(client: TestClient) -> None:
    response = client.post(
        "/api/recording-sessions",
        json={"title": "测试长录音", "chunk_duration_seconds": 180},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "测试长录音"
    assert payload["status"] == "recording"
    assert payload["chunk_duration_seconds"] == 180
    assert payload["chunks"] == []
    assert payload["started_at"]


def test_create_recording_session_rejects_invalid_chunk_duration(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/recording-sessions",
        json={"title": "非法分段", "chunk_duration_seconds": 45},
    )

    assert response.status_code == 400
    assert "分段时长" in response.json()["detail"]


def test_upload_recording_session_chunk_creates_recording_and_chunk(
    client: TestClient,
) -> None:
    session_response = client.post(
        "/api/recording-sessions",
        json={"title": "长录音", "chunk_duration_seconds": 30},
    )
    session_id = session_response.json()["id"]

    response = client.post(
        f"/api/recording-sessions/{session_id}/chunks",
        data={
            "chunk_index": "1",
            "start_offset_seconds": "0",
            "end_offset_seconds": "30",
        },
        files={
            "file": (
                "session-1-chunk-1.webm",
                BytesIO(b"fake chunk bytes"),
                "audio/webm",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["chunk_index"] == 1
    assert payload["start_offset_seconds"] == 0
    assert payload["end_offset_seconds"] == 30
    assert payload["status"] == "uploaded"
    assert payload["recording_id"]
    assert payload["recording"]["original_filename"] == "session-1-chunk-1.webm"

    recording_response = client.get(f"/api/recordings/{payload['recording_id']}")
    assert recording_response.status_code == 200


def test_recording_session_detail_returns_chunks(client: TestClient) -> None:
    session_response = client.post(
        "/api/recording-sessions",
        json={"title": "长录音详情", "chunk_duration_seconds": 30},
    )
    session_id = session_response.json()["id"]
    assert (
        client.post(
            f"/api/recording-sessions/{session_id}/chunks",
            data={
                "chunk_index": "1",
                "start_offset_seconds": "0",
                "end_offset_seconds": "30",
            },
            files={
                "file": (
                    "session-detail-chunk.webm",
                    BytesIO(b"fake chunk bytes"),
                    "audio/webm",
                )
            },
        ).status_code
        == 201
    )

    response = client.get(f"/api/recording-sessions/{session_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == session_id
    assert len(payload["chunks"]) == 1
    assert payload["chunks"][0]["recording"]["original_filename"] == (
        "session-detail-chunk.webm"
    )


def test_update_recording_session_and_chunk_status(client: TestClient) -> None:
    session_response = client.post(
        "/api/recording-sessions",
        json={"title": "状态更新", "chunk_duration_seconds": 30},
    )
    session_id = session_response.json()["id"]
    chunk_response = client.post(
        f"/api/recording-sessions/{session_id}/chunks",
        data={
            "chunk_index": "1",
            "start_offset_seconds": "0",
            "end_offset_seconds": "30",
        },
        files={
            "file": (
                "session-status-chunk.webm",
                BytesIO(b"fake chunk bytes"),
                "audio/webm",
            )
        },
    )
    chunk_id = chunk_response.json()["id"]

    chunk_update = client.patch(
        f"/api/recording-sessions/{session_id}/chunks/{chunk_id}",
        json={"status": "transcribing", "error_message": None},
    )
    session_update = client.patch(
        f"/api/recording-sessions/{session_id}",
        json={"status": "completed"},
    )

    assert chunk_update.status_code == 200
    assert chunk_update.json()["status"] == "transcribing"
    assert chunk_update.json()["error_message"] is None
    assert session_update.status_code == 200
    assert session_update.json()["status"] == "completed"
    assert session_update.json()["stopped_at"]


def test_upload_rejects_unsupported_file(client: TestClient) -> None:
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("notes.txt", BytesIO(b"not audio"), "text/plain")},
    )

    assert response.status_code == 400
    assert client.get("/api/recordings").json() == []


def test_list_detail_and_audio_response(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.wav", BytesIO(b"fake wav bytes"), "audio/wav")},
    )
    recording_id = upload_response.json()["id"]

    list_response = client.get("/api/recordings")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == recording_id

    detail_response = client.get(f"/api/recordings/{recording_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["original_filename"] == "team.wav"

    audio_response = client.get(f"/api/recordings/{recording_id}/audio")
    assert audio_response.status_code == 200
    assert audio_response.headers["content-type"].startswith("audio/wav")
    assert audio_response.content == b"fake wav bytes"


def test_missing_recording_returns_404(client: TestClient) -> None:
    assert client.get("/api/recordings/missing").status_code == 404
    assert client.get("/api/recordings/missing/audio").status_code == 404


def test_segments_are_empty_before_mock_generation(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]

    response = client.get(f"/api/recordings/{recording_id}/segments")

    assert response.status_code == 200
    assert response.json() == []


def test_generate_mock_segments_replaces_existing_segments(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]

    first_response = client.post(f"/api/recordings/{recording_id}/segments/mock")
    second_response = client.post(f"/api/recordings/{recording_id}/segments/mock")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_segments = first_response.json()
    second_segments = second_response.json()
    assert len(first_segments) == 5
    assert len(second_segments) == 5
    assert {segment["source"] for segment in second_segments} == {"mock"}
    assert [segment["text"] for segment in second_segments] == [
        "兄弟们这波可以打",
        "别急，对面打野不见了",
        "我有大，我先开",
        "我绕后了，等我位置",
        "可以可以，直接开",
    ]
    assert [segment["id"] for segment in first_segments] != [
        segment["id"] for segment in second_segments
    ]

    list_response = client.get(f"/api/recordings/{recording_id}/segments")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 5
    assert list_response.json()[0]["display_speaker_label"] == "Speaker 1"
    assert list_response.json()[0]["is_edited"] is False
    assert list_response.json()[0]["updated_at"]


def test_update_segment_text_persists_and_marks_edited(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    segments = client.post(f"/api/recordings/{recording_id}/segments/mock").json()
    segment_id = segments[0]["id"]

    response = client.patch(
        f"/api/recordings/{recording_id}/segments/{segment_id}",
        json={"text": "兄弟们这波先别急，等信息"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "兄弟们这波先别急，等信息"
    assert payload["is_edited"] is True
    assert payload["updated_at"] >= payload["created_at"]

    list_response = client.get(f"/api/recordings/{recording_id}/segments")
    assert list_response.status_code == 200
    assert list_response.json()[0]["text"] == "兄弟们这波先别急，等信息"
    assert list_response.json()[0]["is_edited"] is True


def test_update_segment_rejects_wrong_recording_or_empty_text(
    client: TestClient,
) -> None:
    first_upload = client.post(
        "/api/recordings/upload",
        files={"file": ("one.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    second_upload = client.post(
        "/api/recordings/upload",
        files={"file": ("two.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    first_id = first_upload.json()["id"]
    second_id = second_upload.json()["id"]
    segment_id = client.post(f"/api/recordings/{first_id}/segments/mock").json()[0][
        "id"
    ]

    missing_response = client.patch(
        f"/api/recordings/{second_id}/segments/{segment_id}",
        json={"text": "不属于这条录音"},
    )
    empty_response = client.patch(
        f"/api/recordings/{first_id}/segments/{segment_id}",
        json={"text": "   "},
    )

    assert missing_response.status_code == 404
    assert empty_response.status_code == 400


def test_speaker_label_rename_persists_and_updates_segments(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201

    labels_response = client.get(f"/api/recordings/{recording_id}/speaker-labels")
    assert labels_response.status_code == 200
    assert labels_response.json()[0]["source_label"] == "Speaker 1"
    assert labels_response.json()[0]["display_name"] == "Speaker 1"

    rename_response = client.patch(
        f"/api/recordings/{recording_id}/speaker-labels",
        json={"source_label": "Speaker 1", "display_name": "主持人"},
    )

    assert rename_response.status_code == 200
    assert rename_response.json()["display_name"] == "主持人"

    refreshed_labels = client.get(
        f"/api/recordings/{recording_id}/speaker-labels"
    ).json()
    assert next(
        label for label in refreshed_labels if label["source_label"] == "Speaker 1"
    )["display_name"] == "主持人"

    refreshed_segments = client.get(f"/api/recordings/{recording_id}/segments").json()
    assert {
        segment["display_speaker_label"]
        for segment in refreshed_segments
        if segment["speaker_label"] == "Speaker 1"
    } == {"主持人"}


def test_speaker_label_rename_rejects_unknown_source_label(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201

    response = client.patch(
        f"/api/recordings/{recording_id}/speaker-labels",
        json={"source_label": "Channel 9", "display_name": "主持人"},
    )

    assert response.status_code == 404


def test_segments_for_missing_recording_return_404(client: TestClient) -> None:
    assert client.get("/api/recordings/missing/segments").status_code == 404
    assert client.post("/api/recordings/missing/segments/mock").status_code == 404
    assert client.post("/api/recordings/missing/transcribe").status_code == 404
    assert client.get("/api/recordings/missing/analysis").status_code == 404
    assert client.post("/api/recordings/missing/analyze").status_code == 404


def test_transcribe_without_dashscope_key_returns_clear_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "load_env_file", lambda _: None)
    monkeypatch.setenv("ASR_PROVIDER", "aliyun")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]

    response = client.post(f"/api/recordings/{recording_id}/transcribe")

    assert response.status_code == 400
    assert "DASHSCOPE_API_KEY" in response.json()["detail"]


def test_transcribe_with_local_public_base_url_returns_clear_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "load_env_file", lambda _: None)
    monkeypatch.setenv("ASR_PROVIDER", "aliyun")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.wav", BytesIO(b"fake wav bytes"), "audio/wav")},
    )
    recording_id = upload_response.json()["id"]

    response = client.post(f"/api/recordings/{recording_id}/transcribe")

    assert response.status_code == 400
    assert "阿里云无法访问本地音频 URL" in response.json()["detail"]


def test_parse_aliyun_transcription_json_converts_sentences_to_segments() -> None:
    segments = parse_aliyun_transcription_json(
        {
            "result": {
                "transcripts": [
                    {
                        "channel_id": 0,
                        "sentences": [
                            {
                                "begin_time": 1200,
                                "end_time": 3200,
                                "text": "中路可以推",
                            },
                            {
                                "begin_time": 3200,
                                "end_time": 6100,
                                "text": "我在河道看视野",
                            },
                        ],
                    }
                ]
            }
        }
    )

    assert len(segments) == 2
    assert segments[0].start_time == 1.2
    assert segments[0].end_time == 3.2
    assert segments[0].text == "中路可以推"
    assert segments[0].speaker_label == "Channel 0"
    assert segments[0].source == "aliyun"


def test_transcribe_success_saves_segments(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeASRProvider:
        def transcribe(self, recording, public_audio_url: str) -> list[ASRSegment]:
            assert recording.original_filename == "team.mp3"
            assert public_audio_url.endswith(
                f"/api/recordings/{recording.id}/audio"
            )
            return [
                ASRSegment(
                    speaker_label="Speaker 1",
                    start_time=0.5,
                    end_time=2.0,
                    text="真实转写文本",
                    source="aliyun",
                )
            ]

    monkeypatch.setenv("ASR_PROVIDER", "aliyun")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://example.ngrok-free.app")
    monkeypatch.setattr(
        transcriptions,
        "get_asr_provider",
        lambda settings: FakeASRProvider(),
    )

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    mock_response = client.post(f"/api/recordings/{recording_id}/segments/mock")
    assert mock_response.status_code == 201

    response = client.post(f"/api/recordings/{recording_id}/transcribe")

    assert response.status_code == 201
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["text"] == "真实转写文本"
    assert payload[0]["source"] == "aliyun"

    segments_response = client.get(f"/api/recordings/{recording_id}/segments")
    assert segments_response.status_code == 200
    assert segments_response.json() == payload


def test_analyze_without_segments_returns_clear_error(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]

    response = client.post(f"/api/recordings/{recording_id}/analyze")

    assert response.status_code == 400
    assert "请先完成转写" in response.json()["detail"]
    assert "AI 总结" in response.json()["detail"]


def test_mock_analyze_saves_and_returns_analysis(client: TestClient) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201

    response = client.post(f"/api/recordings/{recording_id}/analyze")

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-summary-v1"
    assert payload["title"] == "录音内容摘要"
    assert payload["summary"]
    assert payload["key_points"] == [
        "已成功读取转写文本",
        "AI 总结模块可以正常展示",
        "后续可接入真实 LLM 生成自然总结",
    ]
    assert payload["timeline_summary"] == []
    assert payload["notes"] == ["当前为 mock 结果，不代表真实内容分析"]
    assert payload["is_stale"] is False

    persisted_response = client.get(f"/api/recordings/{recording_id}/analysis")
    assert persisted_response.status_code == 200
    assert persisted_response.json()["id"] == payload["id"]
    assert persisted_response.json()["is_stale"] is False


def test_analysis_becomes_stale_after_segment_or_speaker_label_edit(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    segments = client.post(f"/api/recordings/{recording_id}/segments/mock").json()

    analysis_response = client.post(f"/api/recordings/{recording_id}/analyze")
    assert analysis_response.status_code == 201
    assert analysis_response.json()["is_stale"] is False

    edit_response = client.patch(
        f"/api/recordings/{recording_id}/segments/{segments[0]['id']}",
        json={"text": "这是用户修正后的转写文本"},
    )
    assert edit_response.status_code == 200

    stale_response = client.get(f"/api/recordings/{recording_id}/analysis")
    assert stale_response.status_code == 200
    assert stale_response.json()["is_stale"] is True

    refreshed_analysis = client.post(f"/api/recordings/{recording_id}/analyze")
    assert refreshed_analysis.status_code == 201
    assert refreshed_analysis.json()["is_stale"] is False

    rename_response = client.patch(
        f"/api/recordings/{recording_id}/speaker-labels",
        json={"source_label": "Speaker 1", "display_name": "主持人"},
    )
    assert rename_response.status_code == 200

    stale_after_label = client.get(f"/api/recordings/{recording_id}/analysis")
    assert stale_after_label.status_code == 200
    assert stale_after_label.json()["is_stale"] is True


def test_legacy_mock_review_is_serialized_as_generic_summary(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]

    with SessionLocal() as db:
        db.add(
            RecordingAnalysis(
                recording_id=recording_id,
                provider="mock",
                model="mock-review-v1",
                analysis_json=json.dumps(
                    {
                        "summary": "这段语音围绕团队协作和即时决策展开。",
                        "key_moments": [
                            {
                                "title": "关键沟通片段",
                                "start_time": 0,
                                "end_time": 1,
                                "reason": "旧版模板内容",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                raw_response_json="{}",
            )
        )
        db.commit()

    response = client.get(f"/api/recordings/{recording_id}/analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "mock-review-v1"
    assert "团队协作" not in payload["summary"]
    assert payload["key_points"][0] == "已成功读取转写文本"
    assert payload["notes"] == [
        "当前为旧版 mock 结果，不代表真实内容分析；重新生成后会刷新为新版 AI 总结。"
    ]


def test_dashscope_analyze_without_key_returns_clear_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "load_env_file", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "dashscope")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.wav", BytesIO(b"fake wav bytes"), "audio/wav")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201

    response = client.post(f"/api/recordings/{recording_id}/analyze")

    assert response.status_code == 400
    assert "DASHSCOPE_API_KEY" in response.json()["detail"]


def test_dashscope_analyze_success_saves_provider_model_and_summary(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            content = json.dumps(
                {
                    "title": "测试录音摘要",
                    "summary": "这段录音提到可以行动、需要等待信息，以及后续配合。",
                    "key_points": ["已读取真实转写内容", "讨论了行动时机"],
                    "timeline_summary": [
                        {
                            "start_time": 0,
                            "end_time": 3,
                            "summary": "开头提出可以行动。",
                        }
                    ],
                    "notes": [],
                },
                ensure_ascii=False,
            )
            return json.dumps(
                {"choices": [{"message": {"content": content}}]},
                ensure_ascii=False,
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert request.full_url == (
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        )
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "qwen-plus"
        assert "兄弟们这波可以打" in body["messages"][1]["content"]
        assert "主持人 (Speaker 1)" in body["messages"][1]["content"]
        return FakeResponse()

    monkeypatch.setattr(config, "load_env_file", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("DASHSCOPE_LLM_MODEL", "qwen-plus")
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201
    assert (
        client.patch(
            f"/api/recordings/{recording_id}/speaker-labels",
            json={"source_label": "Speaker 1", "display_name": "主持人"},
        ).status_code
        == 200
    )

    response = client.post(f"/api/recordings/{recording_id}/analyze")

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider"] == "dashscope"
    assert payload["model"] == "qwen-plus"
    assert payload["title"] == "测试录音摘要"
    assert payload["key_points"] == ["已读取真实转写内容", "讨论了行动时机"]
    assert "当前为 mock 总结" not in payload["summary"]
    assert payload["is_stale"] is False

    persisted_response = client.get(f"/api/recordings/{recording_id}/analysis")
    assert persisted_response.status_code == 200
    assert persisted_response.json()["provider"] == "dashscope"


def test_dashscope_analyze_failure_does_not_fallback_to_mock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_urlopen(request, timeout):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr(config, "load_env_file", lambda _: None)
    monkeypatch.setenv("LLM_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)

    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("team.mp3", BytesIO(b"fake mp3 bytes"), "audio/mpeg")},
    )
    recording_id = upload_response.json()["id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201

    response = client.post(f"/api/recordings/{recording_id}/analyze")

    assert response.status_code == 502
    assert "dashscope 请求失败" in response.json()["detail"]
    assert client.get(f"/api/recordings/{recording_id}/analysis").status_code == 404


def test_session_summary_without_chunks_returns_clear_error(
    client: TestClient,
) -> None:
    session = create_test_session(client, "空 session")

    response = client.post(f"/api/recording-sessions/{session['id']}/summary")

    assert response.status_code == 400
    assert "暂无 chunks" in response.json()["detail"]


def test_session_summary_without_transcripts_returns_clear_error(
    client: TestClient,
) -> None:
    session = create_test_session(client, "无转写 session")
    upload_test_session_chunk(client, session["id"], 1, 0, 30)

    response = client.post(f"/api/recording-sessions/{session['id']}/summary")

    assert response.status_code == 400
    assert "至少一个 chunk 转写" in response.json()["detail"]


def test_mock_session_summary_saves_and_returns_ordered_chunks(
    client: TestClient,
) -> None:
    session = create_test_session(client, "整场总结 session")
    second_chunk = upload_test_session_chunk(client, session["id"], 2, 30, 60)
    first_chunk = upload_test_session_chunk(client, session["id"], 1, 0, 30)

    for chunk in (second_chunk, first_chunk):
        recording_id = chunk["recording_id"]
        assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201
        assert client.post(f"/api/recordings/{recording_id}/analyze").status_code == 201

    response = client.post(f"/api/recording-sessions/{session['id']}/summary")

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-session-summary-v1"
    assert payload["title"] == "整场录音摘要"
    assert payload["is_stale"] is False
    assert [item["chunk_index"] for item in payload["chunk_summaries"]] == [1, 2]
    assert payload["chunk_summaries"][0]["start_time"] == 0
    assert payload["chunk_summaries"][1]["start_time"] == 30

    persisted_response = client.get(f"/api/recording-sessions/{session['id']}/summary")
    assert persisted_response.status_code == 200
    assert persisted_response.json()["id"] == payload["id"]
    assert persisted_response.json()["chunk_summaries"][0]["chunk_index"] == 1


def test_session_summary_exports_markdown_and_text(client: TestClient) -> None:
    session = create_test_session(client, "导出 session")
    chunk = upload_test_session_chunk(client, session["id"], 1, 0, 30)
    recording_id = chunk["recording_id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201
    assert client.post(f"/api/recordings/{recording_id}/analyze").status_code == 201
    assert client.post(f"/api/recording-sessions/{session['id']}/summary").status_code == 201

    markdown_response = client.get(f"/api/recording-sessions/{session['id']}/export.md")
    text_response = client.get(f"/api/recording-sessions/{session['id']}/export.txt")

    assert markdown_response.status_code == 200
    assert markdown_response.headers["content-type"].startswith("text/markdown")
    assert "# 整场录音摘要" in markdown_response.text
    assert "## 整体总结" in markdown_response.text
    assert "provider: mock" in markdown_response.text

    assert text_response.status_code == 200
    assert text_response.headers["content-type"].startswith("text/plain")
    assert "整场录音摘要" in text_response.text
    assert "整体总结" in text_response.text


def test_session_summary_becomes_stale_after_chunk_analysis_refresh(
    client: TestClient,
) -> None:
    session = create_test_session(client, "过期提示 session")
    chunk = upload_test_session_chunk(client, session["id"], 1, 0, 30)
    recording_id = chunk["recording_id"]
    assert client.post(f"/api/recordings/{recording_id}/segments/mock").status_code == 201
    assert client.post(f"/api/recordings/{recording_id}/analyze").status_code == 201

    summary_response = client.post(f"/api/recording-sessions/{session['id']}/summary")
    assert summary_response.status_code == 201
    assert summary_response.json()["is_stale"] is False

    refreshed_analysis = client.post(f"/api/recordings/{recording_id}/analyze")
    assert refreshed_analysis.status_code == 201

    stale_response = client.get(f"/api/recording-sessions/{session['id']}/summary")
    assert stale_response.status_code == 200
    assert stale_response.json()["is_stale"] is True
