from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .config import Settings, get_settings
from .models import TranscriptSegment

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMAnalysisResult:
    provider: str
    model: str
    analysis: dict[str, Any]
    raw_response: dict[str, Any]


class LLMProviderError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class LLMProvider(Protocol):
    def analyze(
        self,
        segments: list[TranscriptSegment],
        speaker_label_map: dict[str, str] | None = None,
    ) -> LLMAnalysisResult:
        pass

    def summarize_session(
        self,
        chunks: list[dict[str, Any]],
    ) -> LLMAnalysisResult:
        pass


class MockLLMProvider:
    provider = "mock"
    model = "mock-summary-v1"
    session_model = "mock-session-summary-v1"

    def analyze(
        self,
        segments: list[TranscriptSegment],
        speaker_label_map: dict[str, str] | None = None,
    ) -> LLMAnalysisResult:
        analysis = normalize_analysis_payload(generic_mock_summary_payload(), segments)

        return LLMAnalysisResult(
            provider=self.provider,
            model=self.model,
            analysis=analysis,
            raw_response={"provider": self.provider, "analysis": analysis},
        )

    def summarize_session(
        self,
        chunks: list[dict[str, Any]],
    ) -> LLMAnalysisResult:
        analysis = normalize_session_summary_payload(
            generic_mock_session_summary_payload(chunks),
            chunks,
        )

        return LLMAnalysisResult(
            provider=self.provider,
            model=self.session_model,
            analysis=analysis,
            raw_response={"provider": self.provider, "analysis": analysis},
        )


def generic_mock_summary_payload(
    note: str = "当前为 mock 结果，不代表真实内容分析",
) -> dict[str, Any]:
    return {
        "title": "录音内容摘要",
        "summary": (
            "这段录音主要围绕若干话题展开，具体内容取决于转写文本。"
            "当前为 mock 总结，仅用于验证展示流程。"
        ),
        "key_points": [
            "已成功读取转写文本",
            "AI 总结模块可以正常展示",
            "后续可接入真实 LLM 生成自然总结",
        ],
        "timeline_summary": [],
        "notes": [note],
    }


def generic_mock_session_summary_payload(
    chunks: list[dict[str, Any]],
    note: str = "当前为 mock 结果，不代表真实整场内容分析",
) -> dict[str, Any]:
    chunk_summaries: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    notes = [note]

    for chunk in sorted(chunks, key=lambda item: int(item.get("chunk_index", 0))):
        chunk_index = int(chunk.get("chunk_index", 0))
        start_time = float(chunk.get("start_time", 0))
        end_time = float(chunk.get("end_time", start_time))
        transcript = clean_string(chunk.get("transcript"))
        chunk_summary = clean_string(chunk.get("analysis_summary"))
        if not transcript:
            notes.append(f"第 {chunk_index} 段缺少转写，整场总结可能不完整。")
        if not chunk_summary:
            notes.append(f"第 {chunk_index} 段缺少分段 AI 总结。")

        summary_text = (
            chunk_summary
            or (f"第 {chunk_index} 段已读取转写文本。" if transcript else "该段信息不足。")
        )
        if end_time > start_time:
            chunk_summaries.append(
                {
                    "chunk_index": chunk_index,
                    "start_time": start_time,
                    "end_time": end_time,
                    "summary": summary_text,
                }
            )
            timeline.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "title": f"第 {chunk_index} 段",
                    "summary": summary_text,
                }
            )

    return {
        "title": "整场录音摘要",
        "summary": (
            "这是一份基于多个分段转写和分段总结生成的整场 mock 总结，"
            "用于验证整场总结、持久化和导出流程。"
        ),
        "key_points": [
            "已成功读取长录音分段上下文",
            "整场总结模块可以正常保存和展示",
            "后续可使用真实 LLM 生成自然整场总结",
        ],
        "timeline": timeline,
        "chunk_summaries": chunk_summaries,
        "notes": notes,
    }


class ChatCompletionsLLMProvider:
    provider: str
    model: str
    base_url: str
    api_key: str | None
    api_key_env_name: str
    timeout_seconds: float

    def analyze(
        self,
        segments: list[TranscriptSegment],
        speaker_label_map: dict[str, str] | None = None,
    ) -> LLMAnalysisResult:
        self._validate_settings()
        messages = build_analysis_messages(segments, speaker_label_map)
        response_payload = self._request_chat_completion(messages)
        content = self._extract_content(response_payload)
        parsed = parse_json_content(content)
        analysis = normalize_analysis_payload(parsed, segments)

        return LLMAnalysisResult(
            provider=self.provider,
            model=self.model,
            analysis=analysis,
            raw_response=response_payload,
        )

    def summarize_session(
        self,
        chunks: list[dict[str, Any]],
    ) -> LLMAnalysisResult:
        self._validate_settings()
        messages = build_session_summary_messages(chunks)
        response_payload = self._request_chat_completion(messages)
        content = self._extract_content(response_payload)
        parsed = parse_json_content(content)
        analysis = normalize_session_summary_payload(parsed, chunks)

        return LLMAnalysisResult(
            provider=self.provider,
            model=self.model,
            analysis=analysis,
            raw_response=response_payload,
        )

    def _validate_settings(self) -> None:
        if not self.api_key:
            raise LLMProviderError(
                400,
                f"未配置 {self.api_key_env_name}，无法调用 {self.provider} 生成 AI 总结。",
            )

    def _request_chat_completion(
        self, messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise LLMProviderError(
                502,
                f"{self.provider} 请求失败：HTTP {error.code} {detail[:500]}",
            ) from error
        except urllib.error.URLError as error:
            raise LLMProviderError(
                502,
                f"{self.provider} 请求失败：{error.reason}",
            ) from error
        except TimeoutError as error:
            raise LLMProviderError(502, f"{self.provider} 请求超时。") from error

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as error:
            logger.error("%s returned non-JSON response: %s", self.provider, body)
            raise LLMProviderError(
                502,
                f"{self.provider} 返回了无法解析的 JSON。",
            ) from error

        if not isinstance(decoded, dict):
            raise LLMProviderError(502, f"{self.provider} 返回 JSON 结构不是对象。")

        return decoded

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(502, f"{self.provider} 响应中没有 choices。")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMProviderError(502, f"{self.provider} choices 结构无效。")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMProviderError(502, f"{self.provider} 响应中没有 message。")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(502, f"{self.provider} 响应中没有可用内容。")

        return content


class DashScopeLLMProvider(ChatCompletionsLLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.provider = "dashscope"
        self.model = settings.dashscope_llm_model
        self.base_url = settings.dashscope_llm_base_url
        self.api_key = settings.dashscope_api_key
        self.api_key_env_name = "DASHSCOPE_API_KEY"
        self.timeout_seconds = settings.llm_request_timeout_seconds


class OpenAILLMProvider(ChatCompletionsLLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.provider = "openai"
        self.model = settings.openai_llm_model
        self.base_url = settings.openai_llm_base_url
        self.api_key = settings.openai_api_key
        self.api_key_env_name = "OPENAI_API_KEY"
        self.timeout_seconds = settings.llm_request_timeout_seconds


def build_analysis_messages(
    segments: list[TranscriptSegment],
    speaker_label_map: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    transcript = build_transcript_context(segments, speaker_label_map)
    schema = {
        "title": "一句话标题",
        "summary": "对整段录音的自然总结",
        "key_points": ["重点信息 1", "重点信息 2"],
        "timeline_summary": [
            {
                "start_time": 0,
                "end_time": 15,
                "summary": "这一时间段大致讲了什么",
            }
        ],
        "notes": ["信息不足或需要确认的地方"],
    }

    return [
        {
            "role": "system",
            "content": (
                "你是音频转写总结助手。只根据用户提供的 transcript segments "
                "总结录音内容，不要编造没出现的信息。输出必须是严格 JSON，"
                "不要输出 Markdown。所有内容使用中文。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请基于下面的音频转写生成自然、克制的 AI 总结。"
                "这段音频不一定是游戏语音，请先在内部判断内容类型，"
                "例如游戏语音、会议/访谈、闲聊、讲解、新闻/视频音频或其他，"
                "但不要在返回 JSON 中生硬展示内容类型。不要套模板，不要强行寻找"
                "搞笑、冲突、高光、沟通问题或玩家风格。只总结转写中真实出现的"
                "信息。不要使用“本局”“开团”“资源争夺”“团队协作”等游戏词，"
                "除非转写中确实出现类似内容。如果转写很短、上下文不足或内容不清，"
                "请简短说明“信息较少，无法进一步判断”，不要硬分析。"
                "timeline_summary 中的 start_time 和 end_time 必须来自已有 segments "
                "的时间范围；如果无法合理拆分时间段，可以返回空数组。\n\n"
                f"必须返回这个 JSON schema：\n{json.dumps(schema, ensure_ascii=False)}\n\n"
                f"transcript segments：\n{transcript}"
            ),
        },
    ]


def build_transcript_context(
    segments: list[TranscriptSegment],
    speaker_label_map: dict[str, str] | None = None,
) -> str:
    lines = []
    resolved_label_map = speaker_label_map or {}
    for segment in sorted(segments, key=lambda item: (item.start_time, item.end_time)):
        display_label = resolved_label_map.get(segment.speaker_label)
        speaker_label = (
            f"{display_label} ({segment.speaker_label})"
            if display_label and display_label != segment.speaker_label
            else segment.speaker_label
        )
        lines.append(
            f"[{segment.start_time:.2f}-{segment.end_time:.2f}] "
            f"{speaker_label}: {segment.text}"
        )
    return "\n".join(lines)


def build_session_summary_messages(
    chunks: list[dict[str, Any]],
) -> list[dict[str, str]]:
    context = build_session_summary_context(chunks)
    schema = {
        "title": "整场录音标题",
        "summary": "对整场录音的自然总结",
        "key_points": ["重点 1", "重点 2"],
        "timeline": [
            {
                "start_time": 0,
                "end_time": 180,
                "title": "这一阶段的简短标题",
                "summary": "这一阶段大致讲了什么",
            }
        ],
        "chunk_summaries": [
            {
                "chunk_index": 1,
                "start_time": 0,
                "end_time": 180,
                "summary": "该 chunk 的摘要",
            }
        ],
        "notes": ["信息不足、识别可能有误、需要进一步确认的地方"],
    }

    return [
        {
            "role": "system",
            "content": (
                "你是音频转写总结助手。只根据用户提供的长录音 chunks "
                "总结整场内容，不要编造没出现的信息。输出必须是严格 JSON，"
                "不要输出 Markdown。所有内容使用中文。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请基于下面多个 chunk 的转写和分段总结，生成自然、通用、克制的整场总结。"
                "不要假设这是游戏语音；如果内容是会议，就按会议总结；如果是闲聊，"
                "就按闲聊总结；如果是游戏语音，也只做自然总结，不要套固定模板。"
                "不要强行输出搞笑、冲突、高光片段。只根据已有 transcript 和 chunk summary "
                "分析，不要编造。若某些 chunk 缺少转写或总结，请在 notes 中说明。"
                "timeline 和 chunk_summaries 的时间必须来自已有 chunk 时间范围；"
                "如果无法合理拆分 timeline，可以返回空数组。\n\n"
                f"必须返回这个 JSON schema：\n{json.dumps(schema, ensure_ascii=False)}\n\n"
                f"session chunks：\n{context}"
            ),
        },
    ]


def build_session_summary_context(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for chunk in sorted(chunks, key=lambda item: int(item.get("chunk_index", 0))):
        chunk_index = int(chunk.get("chunk_index", 0))
        start_time = float(chunk.get("start_time", 0))
        end_time = float(chunk.get("end_time", start_time))
        recording_filename = clean_string(chunk.get("recording_filename")) or "未知文件"
        transcript = clean_string(chunk.get("transcript")) or "（缺少转写）"
        analysis_summary = clean_string(chunk.get("analysis_summary")) or "（缺少分段总结）"
        key_points = chunk.get("analysis_key_points")
        key_points_text = ""
        if isinstance(key_points, list) and key_points:
            key_points_text = "\n分段重点：" + "；".join(
                clean_string(item) for item in key_points if clean_string(item)
            )

        lines.append(
            "\n".join(
                [
                    f"Chunk {chunk_index} [{start_time:.2f}-{end_time:.2f}]",
                    f"recording: {recording_filename}",
                    f"分段总结：{analysis_summary}{key_points_text}",
                    f"转写：\n{transcript}",
                ]
            )
        )

    return "\n\n---\n\n".join(lines)


def parse_json_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as error:
        raise LLMProviderError(
            400,
            "LLM 输出不是严格 JSON，无法保存 AI 总结。",
        ) from error

    if not isinstance(payload, dict):
        raise LLMProviderError(400, "LLM 输出 JSON 顶层必须是对象。")

    return payload


def normalize_analysis_payload(
    payload: dict[str, Any], segments: list[TranscriptSegment]
) -> dict[str, Any]:
    time_min = min(segment.start_time for segment in segments)
    time_max = max(segment.end_time for segment in segments)
    return normalize_saved_analysis_payload(payload, time_min, time_max)


def normalize_saved_analysis_payload(
    payload: dict[str, Any],
    time_min: float | None = None,
    time_max: float | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    title = clean_string(payload.get("title")) or "录音内容摘要"
    summary = clean_string(payload.get("summary")) or "信息较少，无法进一步判断。"
    key_points = normalize_string_list(payload.get("key_points"))
    if not key_points:
        key_points = derive_key_points_from_legacy_payload(payload)

    timeline_source = payload.get("timeline_summary")
    if not isinstance(timeline_source, list):
        timeline_source = payload.get("main_events")

    normalized = {
        "title": title,
        "summary": summary,
        "key_points": key_points,
        "timeline_summary": normalize_timeline_summary_items(
            timeline_source if isinstance(timeline_source, list) else [],
            time_min,
            time_max,
        ),
        "notes": normalize_string_list(payload.get("notes")),
    }

    return normalized


def normalize_session_summary_payload(
    payload: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    if chunks:
        time_min = min(float(chunk.get("start_time", 0)) for chunk in chunks)
        time_max = max(float(chunk.get("end_time", 0)) for chunk in chunks)
        chunk_indexes = {
            int(chunk.get("chunk_index"))
            for chunk in chunks
            if chunk.get("chunk_index") is not None
        }
    else:
        time_min = None
        time_max = None
        chunk_indexes = None

    return normalize_saved_session_summary_payload(
        payload,
        time_min=time_min,
        time_max=time_max,
        allowed_chunk_indexes=chunk_indexes,
    )


def normalize_saved_session_summary_payload(
    payload: dict[str, Any],
    time_min: float | None = None,
    time_max: float | None = None,
    allowed_chunk_indexes: set[int] | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    title = clean_string(payload.get("title")) or "整场录音摘要"
    summary = clean_string(payload.get("summary")) or "信息较少，无法进一步判断。"

    timeline_source = payload.get("timeline")
    if not isinstance(timeline_source, list):
        timeline_source = []

    chunk_summaries_source = payload.get("chunk_summaries")
    if not isinstance(chunk_summaries_source, list):
        chunk_summaries_source = []

    return {
        "title": title,
        "summary": summary,
        "key_points": normalize_string_list(payload.get("key_points")),
        "timeline": normalize_session_timeline_items(
            timeline_source,
            time_min,
            time_max,
        ),
        "chunk_summaries": normalize_session_chunk_summary_items(
            chunk_summaries_source,
            time_min,
            time_max,
            allowed_chunk_indexes,
        ),
        "notes": normalize_string_list(payload.get("notes")),
    }


def clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := clean_string(item))]


def derive_key_points_from_legacy_payload(payload: dict[str, Any]) -> list[str]:
    key_points: list[str] = []
    for field in ("key_moments", "main_events", "communication_issues", "suggestions"):
        value = payload.get(field)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str):
                text = clean_string(item)
            elif isinstance(item, dict):
                text = (
                    clean_string(item.get("title"))
                    or clean_string(item.get("description"))
                    or clean_string(item.get("reason"))
                    or clean_string(item.get("issue"))
                    or clean_string(item.get("suggestion"))
                )
            else:
                text = ""
            if text:
                key_points.append(text)
            if len(key_points) >= 5:
                return key_points
    return key_points


def normalize_timeline_summary_items(
    items: list[Any], time_min: float | None = None, time_max: float | None = None
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            start_time = float(item.get("start_time"))
            end_time = float(item.get("end_time"))
        except (TypeError, ValueError):
            continue

        if end_time <= start_time:
            continue
        if time_min is not None and start_time < time_min:
            continue
        if time_max is not None and end_time > time_max:
            continue

        summary = (
            clean_string(item.get("summary"))
            or clean_string(item.get("description"))
            or clean_string(item.get("reason"))
            or clean_string(item.get("evidence"))
            or clean_string(item.get("suggestion"))
            or clean_string(item.get("title"))
        )
        if not summary:
            continue

        normalized.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "summary": summary,
            }
        )

    return normalized


def normalize_session_timeline_items(
    items: list[Any], time_min: float | None = None, time_max: float | None = None
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            start_time = float(item.get("start_time"))
            end_time = float(item.get("end_time"))
        except (TypeError, ValueError):
            continue

        if end_time <= start_time:
            continue
        if time_min is not None and start_time < time_min:
            continue
        if time_max is not None and end_time > time_max:
            continue

        summary = clean_string(item.get("summary"))
        if not summary:
            continue

        normalized.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "title": clean_string(item.get("title")) or "阶段摘要",
                "summary": summary,
            }
        )

    return normalized


def normalize_session_chunk_summary_items(
    items: list[Any],
    time_min: float | None = None,
    time_max: float | None = None,
    allowed_chunk_indexes: set[int] | None = None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            chunk_index = int(item.get("chunk_index"))
            start_time = float(item.get("start_time"))
            end_time = float(item.get("end_time"))
        except (TypeError, ValueError):
            continue

        if allowed_chunk_indexes is not None and chunk_index not in allowed_chunk_indexes:
            continue
        if end_time <= start_time:
            continue
        if time_min is not None and start_time < time_min:
            continue
        if time_max is not None and end_time > time_max:
            continue

        summary = clean_string(item.get("summary"))
        if not summary:
            continue

        normalized.append(
            {
                "chunk_index": chunk_index,
                "start_time": start_time,
                "end_time": end_time,
                "summary": summary,
            }
        )

    return sorted(normalized, key=lambda item: item["chunk_index"])


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    resolved_settings = settings or get_settings()
    if resolved_settings.llm_provider == "mock":
        return MockLLMProvider()
    if resolved_settings.llm_provider == "dashscope":
        return DashScopeLLMProvider(resolved_settings)
    if resolved_settings.llm_provider == "openai":
        return OpenAILLMProvider(resolved_settings)

    raise LLMProviderError(
        400,
        f"不支持的 LLM_PROVIDER：{resolved_settings.llm_provider}。",
    )
