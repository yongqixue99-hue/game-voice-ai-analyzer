from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from .config import Settings, get_settings
from .models import Recording

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ASRSegment:
    speaker_label: str
    start_time: float
    end_time: float
    text: str
    source: str


class ASRProviderError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ASRProvider(Protocol):
    def transcribe(
        self, recording: Recording, public_audio_url: str
    ) -> list[ASRSegment]:
        pass


MOCK_SEGMENTS = (
    (0.0, 3.0, "Speaker 1", "兄弟们这波可以打"),
    (3.0, 7.0, "Speaker 2", "别急，对面打野不见了"),
    (7.0, 12.0, "Speaker 1", "我有大，我先开"),
    (12.0, 18.0, "Speaker 3", "我绕后了，等我位置"),
    (18.0, 24.0, "Speaker 2", "可以可以，直接开"),
)


class MockASRProvider:
    def transcribe(
        self, recording: Recording, public_audio_url: str
    ) -> list[ASRSegment]:
        segments: list[ASRSegment] = []
        duration = recording.duration

        for start_time, end_time, speaker_label, text in MOCK_SEGMENTS:
            if duration is not None:
                if start_time >= duration:
                    continue
                end_time = min(end_time, duration)
                if end_time <= start_time:
                    continue

            segments.append(
                ASRSegment(
                    speaker_label=speaker_label,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    source="mock",
                )
            )

        return segments


class AliyunASRProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def transcribe(
        self, recording: Recording, public_audio_url: str
    ) -> list[ASRSegment]:
        self._validate_settings()
        task_id = self._submit_task(public_audio_url)
        task_payload = self._poll_task(task_id)
        transcription_urls = self._extract_transcription_urls(task_payload)

        segments: list[ASRSegment] = []
        for transcription_url in transcription_urls:
            result_payload = self._request_json(transcription_url, method="GET")
            segments.extend(parse_aliyun_transcription_json(result_payload))

        if not segments:
            logger.error("Aliyun ASR returned no usable segments: %s", task_payload)
            raise ASRProviderError(
                400,
                "阿里云识别结果没有可用的句级时间戳，无法生成转写时间轴。",
            )

        return sorted(segments, key=lambda segment: (segment.start_time, segment.end_time))

    def _validate_settings(self) -> None:
        if not self.settings.dashscope_api_key:
            raise ASRProviderError(400, "未配置 DASHSCOPE_API_KEY，无法调用阿里云转写。")

        parsed_base_url = urllib.parse.urlparse(self.settings.public_base_url)
        hostname = parsed_base_url.hostname
        if not parsed_base_url.scheme or not hostname:
            raise ASRProviderError(400, "PUBLIC_BASE_URL 配置无效，请配置公网后端地址。")

        if hostname in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
            raise ASRProviderError(
                400,
                "阿里云 ASR 无法访问本地音频文件。请配置 PUBLIC_BASE_URL / localtunnel / "
                "OSS 公网 URL，或切换到 FunASR HTTP Provider（ASR_PROVIDER=funasr_http）。",
            )

    def _submit_task(self, public_audio_url: str) -> str:
        payload = {
            "model": self.settings.aliyun_asr_model,
            "input": {"file_urls": [public_audio_url]},
            "parameters": {
                "channel_id": [0],
                "language_hints": ["zh", "en"],
            },
        }
        response_payload = self._request_json(
            f"{self.settings.aliyun_dashscope_base_url}/services/audio/asr/transcription",
            method="POST",
            payload=payload,
            headers={
                "Authorization": f"Bearer {self.settings.dashscope_api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
        )

        output = response_payload.get("output")
        task_id = (
            output.get("task_id")
            if isinstance(output, dict)
            else response_payload.get("task_id")
        )
        if not isinstance(task_id, str) or not task_id:
            logger.error("Aliyun ASR submit response missing task_id: %s", response_payload)
            raise ASRProviderError(502, "阿里云转写任务提交成功但未返回 task_id。")

        return task_id

    def _poll_task(self, task_id: str) -> dict[str, Any]:
        task_url = f"{self.settings.aliyun_dashscope_base_url}/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.settings.dashscope_api_key}"}

        for _ in range(self.settings.aliyun_asr_max_polls):
            payload = self._request_json(task_url, method="GET", headers=headers)
            output = payload.get("output") if isinstance(payload.get("output"), dict) else {}
            task_status = str(
                output.get("task_status") or payload.get("task_status") or ""
            ).upper()

            if task_status in {"SUCCEEDED", "SUCCESS"}:
                return payload
            if task_status in {"FAILED", "CANCELED", "CANCELLED"}:
                logger.error("Aliyun ASR task failed: %s", payload)
                message = output.get("message") or payload.get("message") or "阿里云任务失败。"
                if message == "FILE_DOWNLOAD_FAILED":
                    message = (
                        "阿里云下载音频失败。请确认 PUBLIC_BASE_URL 指向的公网隧道仍在运行，"
                        "并且该公网地址可以直接访问 /api/recordings/{id}/audio 音频文件。"
                    )
                raise ASRProviderError(502, f"阿里云任务失败：{message}")

            time.sleep(self.settings.aliyun_asr_poll_interval_seconds)

        raise ASRProviderError(502, "阿里云转写任务轮询超时。")

    def _extract_transcription_urls(self, task_payload: dict[str, Any]) -> list[str]:
        output = task_payload.get("output") if isinstance(task_payload.get("output"), dict) else {}
        results = output.get("results") or task_payload.get("results") or []

        urls: list[str] = []
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                transcription_url = result.get("transcription_url")
                if isinstance(transcription_url, str) and transcription_url:
                    urls.append(transcription_url)

        if not urls:
            logger.error("Aliyun ASR task response missing transcription_url: %s", task_payload)
            raise ASRProviderError(502, "阿里云任务成功但未返回 transcription_url。")

        return urls

    def _request_json(
        self,
        url: str,
        method: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request_data = None
        if payload is not None:
            request_data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=request_data,
            headers=headers or {},
            method=method,
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.settings.aliyun_asr_request_timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ASRProviderError(
                502,
                f"阿里云请求失败：HTTP {error.code} {detail[:500]}",
            ) from error
        except urllib.error.URLError as error:
            raise ASRProviderError(502, f"阿里云请求失败：{error.reason}") from error
        except TimeoutError as error:
            raise ASRProviderError(502, "阿里云请求超时。") from error

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as error:
            logger.error("Aliyun ASR returned non-JSON response from %s: %s", url, body)
            raise ASRProviderError(502, "阿里云返回了无法解析的 JSON。") from error

        if not isinstance(decoded, dict):
            raise ASRProviderError(502, "阿里云返回 JSON 结构不是对象。")

        return decoded


class FunasrHttpASRProvider:
    """Local / LAN FunASR HTTP provider.

    Unlike aliyun (which downloads a public URL), FunASR receives the audio
    bytes directly via multipart upload, so it works for desktop local files
    with no public URL. LUNARIS only *calls* the FunASR HTTP service; deploying
    FunASR (on this machine / a LAN box / a GPU server) is out of scope.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def transcribe(
        self, recording: Recording, public_audio_url: str
    ) -> list[ASRSegment]:
        # Local import avoids pulling the recordings router module into asr.py.
        from .recordings import resolve_recording_path

        audio_path = resolve_recording_path(recording)
        if not audio_path.exists() or not audio_path.is_file():
            raise ASRProviderError(404, "录音文件不存在，无法发送给 FunASR。")

        url = f"{self.settings.funasr_http_base_url}{self.settings.funasr_http_transcribe_path}"
        body, content_type = _build_multipart_body(
            field_name="audio",
            filename=audio_path.name,
            file_bytes=audio_path.read_bytes(),
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.settings.funasr_http_timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ASRProviderError(
                502, f"FunASR 请求失败：HTTP {error.code} {detail[:500]}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            reason = getattr(error, "reason", error)
            raise ASRProviderError(
                503,
                "FunASR 服务未连接，请先启动本地或局域网 FunASR HTTP 服务。"
                f"（{self.settings.funasr_http_base_url}，{reason}）",
            ) from error

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            logger.error("FunASR returned non-JSON response: %s", raw[:1000])
            raise ASRProviderError(502, "FunASR 返回了无法解析的 JSON。") from error

        segments = parse_funasr_response(payload, recording)
        if not segments:
            logger.error("FunASR returned no usable segments: %s", raw[:1000])
            raise ASRProviderError(
                400, "FunASR 返回结果为空或缺少可用文本，无法生成转写时间轴。"
            )
        return sorted(segments, key=lambda s: (s.start_time, s.end_time))


def _build_multipart_body(
    field_name: str, filename: str, file_bytes: bytes
) -> tuple[bytes, str]:
    """Build a minimal multipart/form-data body using stdlib only."""

    boundary = f"----LunarisFunASR{uuid.uuid4().hex}"
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + file_bytes + tail, f"multipart/form-data; boundary={boundary}"


def _funasr_time_to_seconds(value: Any, *, is_millis: bool) -> float | None:
    """Convert a FunASR timestamp to seconds.

    Unit is decided by field-name convention (passed via ``is_millis``):
    ``begin_time``/``end_time`` are milliseconds (like aliyun), while
    ``start``/``end`` are seconds. As a safety net, a value that is implausibly
    large for seconds (>= 3600 on a field declared as seconds) is also treated
    as milliseconds.
    """

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if is_millis or abs(number) >= 1000:
        return number / 1000.0
    return number


def _looks_like_funasr_segment(payload: dict[str, Any]) -> bool:
    text = payload.get("text") or payload.get("value") or payload.get("sentence")
    has_time = any(
        payload.get(key) is not None
        for key in (
            "start",
            "start_time",
            "ts",
            "begin_time",
            "end",
            "end_time",
            "end_time_s",
            "te",
        )
    )
    return isinstance(text, str) and bool(text.strip()) and has_time


def _extract_funasr_segment_list(payload: Any) -> list[dict[str, Any]]:
    """Find sentence-level lists across common FunASR wrapper shapes."""

    segment_keys = ("segments", "sentences", "sentence_info")
    wrapper_keys = ("result", "results", "data", "output")

    if isinstance(payload, list):
        items: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            nested = _extract_funasr_segment_list(item)
            if nested:
                items.extend(nested)
            elif _looks_like_funasr_segment(item):
                items.append(item)
        return items

    if isinstance(payload, dict):
        for key in segment_keys:
            value = payload.get(key)
            if isinstance(value, list):
                items = [item for item in value if isinstance(item, dict)]
                if items:
                    return items

        for key in wrapper_keys:
            value = payload.get(key)
            nested = _extract_funasr_segment_list(value)
            if nested:
                return nested

        if _looks_like_funasr_segment(payload):
            return [payload]

    return []


def parse_funasr_response(payload: Any, recording: Recording) -> list[ASRSegment]:
    """Convert a (tolerant) FunASR JSON response into unified ASRSegments."""

    items = _extract_funasr_segment_list(payload)
    segments: list[ASRSegment] = []

    for index, item in enumerate(items, start=1):
        text = item.get("text") or item.get("value") or item.get("sentence")
        if not isinstance(text, str) or not text.strip():
            continue

        # Field-name convention decides the unit: begin_time/end_time are ms,
        # start/end/ts/te are seconds.
        start_time = end_time = None
        for key, is_ms in (
            ("start", False),
            ("start_time", False),
            ("ts", False),
            ("begin_time", True),
        ):
            if item.get(key) is not None:
                start_time = _funasr_time_to_seconds(item[key], is_millis=is_ms)
                break
        for key, is_ms in (
            ("end", False),
            ("end_time_s", False),
            ("te", False),
            ("end_time", True),
        ):
            if item.get(key) is not None:
                end_time = _funasr_time_to_seconds(item[key], is_millis=is_ms)
                break
        if start_time is None:
            start_time = 0.0
        if end_time is None or end_time < start_time:
            end_time = start_time

        speaker = item.get("speaker") or item.get("speaker_label")
        if not (isinstance(speaker, str) and speaker.strip()):
            spk = item.get("spk")
            speaker = f"Speaker {spk}" if spk is not None else f"Speaker {index}"

        segments.append(
            ASRSegment(
                speaker_label=str(speaker).strip(),
                start_time=start_time,
                end_time=end_time,
                text=text.strip(),
                source="funasr_http",
            )
        )

    # Fallback: a plain full-text response with no per-segment timestamps.
    if not segments:
        full_text = None
        if isinstance(payload, dict):
            full_text = payload.get("text") or payload.get("transcript")
        if isinstance(full_text, str) and full_text.strip():
            duration = recording.duration or 0.0
            segments.append(
                ASRSegment(
                    speaker_label="Speaker 1",
                    start_time=0.0,
                    end_time=float(duration),
                    text=full_text.strip(),
                    source="funasr_http",
                )
            )

    return segments


def parse_aliyun_transcription_json(payload: dict[str, Any]) -> list[ASRSegment]:
    transcripts = extract_transcripts(payload)
    segments: list[ASRSegment] = []

    for transcript_index, transcript in enumerate(transcripts, start=1):
        sentences = transcript.get("sentences")
        if not isinstance(sentences, list):
            continue

        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue

            text = sentence.get("text")
            if not isinstance(text, str) or not text.strip():
                continue

            begin_time = sentence.get("begin_time")
            end_time = sentence.get("end_time")
            if begin_time is None or end_time is None:
                logger.error(
                    "Aliyun ASR sentence missing timestamps: %s",
                    json.dumps(payload, ensure_ascii=False)[:5000],
                )
                raise ASRProviderError(
                    400,
                    "阿里云识别结果缺少句级时间戳，无法生成转写时间轴。",
                )

            segments.append(
                ASRSegment(
                    speaker_label=extract_speaker_label(
                        sentence, transcript, transcript_index
                    ),
                    start_time=millisecond_to_second(begin_time),
                    end_time=millisecond_to_second(end_time),
                    text=text.strip(),
                    source="aliyun",
                )
            )

    if not segments:
        logger.error(
            "Aliyun ASR result did not contain usable sentence timestamps: %s",
            json.dumps(payload, ensure_ascii=False)[:5000],
        )
        raise ASRProviderError(
            400,
            "阿里云识别结果没有可用的句级时间戳，无法生成转写时间轴。",
        )

    return sorted(segments, key=lambda segment: (segment.start_time, segment.end_time))


def extract_transcripts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[Any] = []

    if isinstance(payload.get("transcripts"), list):
        candidates.extend(payload["transcripts"])

    result = payload.get("result")
    if isinstance(result, dict) and isinstance(result.get("transcripts"), list):
        candidates.extend(result["transcripts"])

    output = payload.get("output")
    if isinstance(output, dict):
        output_result = output.get("result")
        if isinstance(output_result, dict) and isinstance(
            output_result.get("transcripts"), list
        ):
            candidates.extend(output_result["transcripts"])

    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def extract_speaker_label(
    sentence: dict[str, Any], transcript: dict[str, Any], transcript_index: int
) -> str:
    for key in ("speaker_label", "speaker"):
        value = sentence.get(key) or transcript.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    speaker_id = (
        sentence["speaker_id"]
        if sentence.get("speaker_id") is not None
        else transcript.get("speaker_id")
    )
    if speaker_id is not None:
        return f"Speaker {speaker_id}"

    channel_id = (
        sentence["channel_id"]
        if sentence.get("channel_id") is not None
        else transcript.get("channel_id")
    )
    if channel_id is not None:
        return f"Channel {channel_id}"

    return f"Speaker {transcript_index}"


def millisecond_to_second(value: Any) -> float:
    try:
        return float(value) / 1000.0
    except (TypeError, ValueError) as error:
        raise ASRProviderError(
            400,
            "阿里云识别结果包含无效时间戳，无法生成转写时间轴。",
        ) from error


def build_public_audio_url(settings: Settings, recording_id: str) -> str:
    return f"{settings.public_base_url}/api/recordings/{recording_id}/audio"


def get_asr_provider(settings: Settings | None = None) -> ASRProvider:
    resolved_settings = settings or get_settings()
    if resolved_settings.asr_provider == "mock":
        return MockASRProvider()
    if resolved_settings.asr_provider == "aliyun":
        return AliyunASRProvider(resolved_settings)
    if resolved_settings.asr_provider == "funasr_http":
        return FunasrHttpASRProvider(resolved_settings)

    raise ASRProviderError(
        400,
        f"不支持的 ASR_PROVIDER：{resolved_settings.asr_provider}。"
        "可选 mock / aliyun / funasr_http。",
    )
