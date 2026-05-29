"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";

type Recording = {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  mime_type: string;
  size_bytes: number;
  duration: number | null;
  status: string;
  created_at: string;
};

type TranscriptSegment = {
  id: string;
  recording_id: string;
  speaker_label: string;
  display_speaker_label: string;
  start_time: number;
  end_time: number;
  text: string;
  source: "mock" | "aliyun" | string;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
};

type SpeakerLabel = {
  source_label: string;
  display_name: string;
  segment_count: number;
  created_at: string | null;
  updated_at: string | null;
};

type TimelineSummaryItem = {
  start_time: number;
  end_time: number;
  summary: string;
};

type RecordingAnalysis = {
  id: string;
  recording_id: string;
  provider: string;
  model: string;
  title: string;
  summary: string;
  key_points: string[];
  timeline_summary: TimelineSummaryItem[];
  notes: string[];
  is_stale: boolean;
  created_at: string;
  updated_at: string;
};

type SessionTimelineItem = {
  start_time: number;
  end_time: number;
  title: string;
  summary: string;
};

type SessionChunkSummaryItem = {
  chunk_index: number;
  start_time: number;
  end_time: number;
  summary: string;
};

type RecordingSessionSummary = {
  id: string;
  session_id: string;
  provider: string;
  model: string;
  title: string;
  summary: string;
  key_points: string[];
  timeline: SessionTimelineItem[];
  chunk_summaries: SessionChunkSummaryItem[];
  notes: string[];
  is_stale: boolean;
  created_at: string;
  updated_at: string;
};

type RecordingSessionChunkStatus =
  | "recording"
  | "uploading"
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "summarizing"
  | "completed"
  | "failed";

type RecordingSessionStatus =
  | "recording"
  | "stopping"
  | "completed"
  | "failed";

type RecordingSessionChunk = {
  id: string;
  session_id: string;
  recording_id: string | null;
  chunk_index: number;
  start_offset_seconds: number;
  end_offset_seconds: number;
  status: RecordingSessionChunkStatus;
  error_message: string | null;
  recording: Recording | null;
  created_at: string;
  updated_at: string;
};

type RecordingSession = {
  id: string;
  title: string;
  status: RecordingSessionStatus;
  chunk_duration_seconds: number;
  started_at: string;
  stopped_at: string | null;
  created_at: string;
  updated_at: string;
  chunks: RecordingSessionChunk[];
};

type BrowserRecordingStatus =
  | "idle"
  | "requesting"
  | "recording"
  | "paused"
  | "stopping"
  | "uploading"
  | "uploaded"
  | "failed";

type AutoAnalysisStatus =
  | "idle"
  | "uploading"
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "summarizing"
  | "completed"
  | "failed";

type AutoAnalysisState = {
  status: AutoAnalysisStatus;
  error: string;
};

type LongRecordingStatus =
  | "idle"
  | "requesting"
  | "recording"
  | "stopping"
  | "completed"
  | "failed";

type NavigationPage = "dashboard" | "library" | "sessions" | "settings";

type AppPage =
  | NavigationPage
  | "recordingDetail"
  | "sessionDetail";

type StatusTone = "success" | "info" | "neutral" | "warning" | "danger";

type LibraryTypeFilter = "all" | "recording" | "session";

type LibraryStatusFilter = "all" | "active" | "completed" | "failed";

type LibraryStatus = "active" | "completed" | "failed";

type LibraryDateGroup = "今天" | "昨天" | "本周" | "更早";

type LibraryItem = {
  id: string;
  kind: "recording" | "session";
  title: string;
  createdAt: string;
  meta: string;
  secondaryMeta: string;
  tags: string[];
  statusLabel: string;
  statusTone: StatusTone;
  statusFilter: LibraryStatus;
};

type AsrServiceOption = "aliyun" | "funasr" | "mock";

type LlmServiceOption = "dashscope" | "openai" | "mock";

type RuntimeEnvironment = "Browser" | "Tauri";

type BackendHealthStatus = "checking" | "connected" | "disconnected";

type BackendHealth = {
  status: "ok" | string;
  service: string;
  version: string;
};

declare global {
  interface Window {
    __LUNARIS_CONFIG__?: {
      apiBaseUrl?: string;
    };
    __TAURI_INTERNALS__?: {
      invoke?: <T = unknown>(cmd: string, args?: Record<string, unknown>) => Promise<T>;
    };
  }
}

const fallbackApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const requestTimeoutMs = 8000;
const healthTimeoutMs = 3000;
const listLoadTimeoutMs = requestTimeoutMs + 1000;
const uploadTimeoutMs = 60000;
const transcribeTimeoutMs = 180000;
const analyzeTimeoutMs = 180000;
const sessionSummaryTimeoutMs = 180000;
const browserRecordingStatusText: Record<BrowserRecordingStatus, string> = {
  idle: "未开始",
  requesting: "请求权限中",
  recording: "录音中",
  paused: "已暂停",
  stopping: "停止中",
  uploading: "上传中",
  uploaded: "上传完成",
  failed: "失败",
};
const longRecordingStatusText: Record<LongRecordingStatus, string> = {
  idle: "未开始",
  requesting: "请求权限中",
  recording: "录音中",
  stopping: "停止中",
  completed: "已完成",
  failed: "失败",
};
const chunkStatusText: Record<RecordingSessionChunkStatus, string> = {
  recording: "录制中",
  uploading: "上传中",
  uploaded: "已上传",
  transcribing: "转写中",
  transcribed: "转写完成",
  summarizing: "总结中",
  completed: "完成",
  failed: "失败",
};
const autoAnalysisStatusText: Record<AutoAnalysisStatus, string> = {
  idle: "未开始",
  uploading: "上传中",
  uploaded: "已上传",
  transcribing: "转写中",
  transcribed: "转写完成",
  summarizing: "总结中",
  completed: "完成",
  failed: "失败",
};
const runningAutoAnalysisStatuses = new Set<AutoAnalysisStatus>([
  "uploading",
  "uploaded",
  "transcribing",
  "transcribed",
  "summarizing",
]);
const chunkDurationOptions = [
  { label: "30 秒（开发测试）", value: 30 },
  { label: "1 分钟", value: 60 },
  { label: "3 分钟", value: 180 },
  { label: "5 分钟", value: 300 },
];
const appNavItems: { key: NavigationPage; label: string; icon: string }[] = [
  { key: "dashboard", label: "控制台", icon: "D" },
  { key: "library", label: "历史记录", icon: "H" },
  { key: "sessions", label: "会话", icon: "S" },
  { key: "settings", label: "设置", icon: "P" },
];
const libraryTypeOptions: { value: LibraryTypeFilter; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "recording", label: "单段录音" },
  { value: "session", label: "长录音会话" },
];
const libraryStatusOptions: { value: LibraryStatusFilter; label: string }[] = [
  { value: "all", label: "全部状态" },
  { value: "active", label: "进行中" },
  { value: "completed", label: "已完成" },
  { value: "failed", label: "失败" },
];
const asrServiceOptions: { value: AsrServiceOption; label: string }[] = [
  { value: "aliyun", label: "阿里云 ASR" },
  { value: "funasr", label: "FunASR 本地" },
  { value: "mock", label: "Mock" },
];
const llmServiceOptions: { value: LlmServiceOption; label: string }[] = [
  { value: "dashscope", label: "DashScope" },
  { value: "openai", label: "OpenAI" },
  { value: "mock", label: "Mock" },
];
const libraryDateGroupOrder: LibraryDateGroup[] = [
  "今天",
  "昨天",
  "本周",
  "更早",
];

function getApiBaseUrl() {
  if (
    typeof window !== "undefined" &&
    window.__LUNARIS_CONFIG__?.apiBaseUrl
  ) {
    return window.__LUNARIS_CONFIG__.apiBaseUrl;
  }
  return fallbackApiBaseUrl;
}

function detectRuntimeEnvironment(): RuntimeEnvironment {
  if (
    typeof window !== "undefined" &&
    typeof window.__TAURI_INTERNALS__ !== "undefined"
  ) {
    return "Tauri";
  }
  return "Browser";
}

type TauriApiBaseUrlInfo = {
  url: string;
  source: "default" | "env:LUNARIS_API_BASE_URL" | "env:LUNARIS_PORT";
};

type TauriRuntimeInfo = {
  runtime: string;
  tauri_version: string;
  app_version: string;
  backend_management_mode: string;
  data_dir_override: string | null;
};

type TauriBackendStatus = {
  mode: string;
  note: string;
  api_base_url: string;
};

const apiBaseUrlSourceLabel: Record<TauriApiBaseUrlInfo["source"], string> = {
  default: "默认值",
  "env:LUNARIS_API_BASE_URL": "环境变量 LUNARIS_API_BASE_URL",
  "env:LUNARIS_PORT": "环境变量 LUNARIS_PORT",
};

async function invokeTauri<T>(cmd: string): Promise<T | null> {
  if (typeof window === "undefined") return null;
  const invoke = window.__TAURI_INTERNALS__?.invoke;
  if (typeof invoke !== "function") return null;
  try {
    return await invoke<T>(cmd);
  } catch {
    return null;
  }
}

function audioUrl(recordingId: string) {
  return `${getApiBaseUrl()}/api/recordings/${recordingId}/audio`;
}

function getApiErrorMessage(error: unknown, fallback: string) {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "无法连接后端服务，请确认 FastAPI 已启动。";
  }
  if (error instanceof TypeError) {
    return "无法连接后端服务，请确认 FastAPI 已启动。";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
  fallbackMessage = "请求失败。",
  timeoutMs = requestTimeoutMs,
) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...options,
      signal: controller.signal,
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string;
      } | null;
      throw new Error(payload?.detail ?? fallbackMessage);
    }

    return (await response.json()) as T;
  } catch (requestError) {
    throw new Error(getApiErrorMessage(requestError, fallbackMessage));
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function requestText(
  path: string,
  options: RequestInit = {},
  fallbackMessage = "请求失败。",
  timeoutMs = requestTimeoutMs,
) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...options,
      signal: controller.signal,
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string;
      } | null;
      throw new Error(payload?.detail ?? fallbackMessage);
    }

    return await response.text();
  } catch (requestError) {
    throw new Error(getApiErrorMessage(requestError, fallbackMessage));
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function fetchRecordings() {
  return requestJson<Recording[]>("/api/recordings", {}, "录音列表加载失败。");
}

async function fetchBackendHealth() {
  return requestJson<BackendHealth>(
    "/api/health",
    {},
    "后端健康检查失败。",
    healthTimeoutMs,
  );
}

async function fetchRecordingSessions() {
  return requestJson<RecordingSession[]>(
    "/api/recording-sessions",
    {},
    "长录音会话加载失败。",
  );
}

async function fetchRecordingSessionSummary(sessionId: string) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, requestTimeoutMs);

  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/recording-sessions/${sessionId}/summary`,
      {
        signal: controller.signal,
      },
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string;
      } | null;
      throw new Error(payload?.detail ?? "整场总结加载失败。");
    }

    return (await response.json()) as RecordingSessionSummary;
  } catch (requestError) {
    throw new Error(getApiErrorMessage(requestError, "整场总结加载失败。"));
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function generateRecordingSessionSummary(sessionId: string) {
  return requestJson<RecordingSessionSummary>(
    `/api/recording-sessions/${sessionId}/summary`,
    {
      method: "POST",
    },
    "整场总结生成失败。",
    sessionSummaryTimeoutMs,
  );
}

async function fetchRecordingSessionExport(
  sessionId: string,
  format: "md" | "txt",
) {
  return requestText(
    `/api/recording-sessions/${sessionId}/export.${format}`,
    {},
    "整场总结导出失败。",
  );
}

async function createRecordingSession(chunkDurationSeconds: number) {
  return requestJson<RecordingSession>(
    "/api/recording-sessions",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: `长录音 ${formatRecordingFilenameDate(new Date())}`,
        chunk_duration_seconds: chunkDurationSeconds,
      }),
    },
    "创建长录音会话失败。",
  );
}

async function updateRecordingSessionStatus(
  sessionId: string,
  statusValue: RecordingSessionStatus,
) {
  return requestJson<RecordingSession>(
    `/api/recording-sessions/${sessionId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: statusValue }),
    },
    "更新长录音会话状态失败。",
  );
}

async function uploadRecordingSessionChunk(
  sessionId: string,
  formData: FormData,
) {
  return requestJson<RecordingSessionChunk>(
    `/api/recording-sessions/${sessionId}/chunks`,
    {
      method: "POST",
      body: formData,
    },
    "上传长录音分段失败。",
    uploadTimeoutMs,
  );
}

async function updateRecordingSessionChunkStatus(
  sessionId: string,
  chunkId: string,
  statusValue: RecordingSessionChunkStatus,
  errorMessage: string | null = null,
) {
  return requestJson<RecordingSessionChunk>(
    `/api/recording-sessions/${sessionId}/chunks/${chunkId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: statusValue,
        error_message: errorMessage,
      }),
    },
    "更新长录音分段状态失败。",
  );
}

async function fetchSegments(recordingId: string) {
  return requestJson<TranscriptSegment[]>(
    `/api/recordings/${recordingId}/segments`,
    {},
    "转写时间轴加载失败。",
  );
}

async function fetchSpeakerLabels(recordingId: string) {
  return requestJson<SpeakerLabel[]>(
    `/api/recordings/${recordingId}/speaker-labels`,
    {},
    "说话人名称加载失败。",
  );
}

async function fetchAnalysis(recordingId: string) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, requestTimeoutMs);

  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/recordings/${recordingId}/analysis`,
      {
        signal: controller.signal,
      },
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string;
      } | null;
      throw new Error(payload?.detail ?? "AI 总结加载失败。");
    }

    return (await response.json()) as RecordingAnalysis;
  } catch (requestError) {
    throw new Error(getApiErrorMessage(requestError, "AI 总结加载失败。"));
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function fetchRecordingsWithSegments() {
  const nextRecordings = await fetchRecordings();
  const entries = await Promise.all(
    nextRecordings.map(async (recording) => {
      let segments: TranscriptSegment[] = [];
      let speakerLabels: SpeakerLabel[] = [];
      let analysis: RecordingAnalysis | null = null;
      let segmentError = "";
      let labelError = "";
      let analysisError = "";

      try {
        segments = await fetchSegments(recording.id);
      } catch (error) {
        segmentError = getApiErrorMessage(error, "转写时间轴加载失败。");
      }

      try {
        speakerLabels = await fetchSpeakerLabels(recording.id);
      } catch (error) {
        labelError = getApiErrorMessage(error, "说话人名称加载失败。");
      }

      try {
        analysis = await fetchAnalysis(recording.id);
      } catch (error) {
        analysisError = getApiErrorMessage(error, "AI 总结加载失败。");
      }

      return {
        recordingId: recording.id,
        segments,
        speakerLabels,
        analysis,
        segmentError,
        labelError,
        analysisError,
      };
    }),
  );

  return {
    recordings: nextRecordings,
    segmentsByRecordingId: Object.fromEntries(
      entries.map((entry) => [entry.recordingId, entry.segments]),
    ) as Record<string, TranscriptSegment[]>,
    segmentErrorsByRecordingId: Object.fromEntries(
      entries
        .filter((entry) => entry.segmentError)
        .map((entry) => [entry.recordingId, entry.segmentError]),
    ) as Record<string, string>,
    speakerLabelsByRecordingId: Object.fromEntries(
      entries.map((entry) => [entry.recordingId, entry.speakerLabels]),
    ) as Record<string, SpeakerLabel[]>,
    labelErrorsByRecordingId: Object.fromEntries(
      entries
        .filter((entry) => entry.labelError)
        .map((entry) => [entry.recordingId, entry.labelError]),
    ) as Record<string, string>,
    analysesByRecordingId: Object.fromEntries(
      entries
        .filter((entry) => entry.analysis)
        .map((entry) => [entry.recordingId, entry.analysis]),
    ) as Record<string, RecordingAnalysis>,
    analysisErrorsByRecordingId: Object.fromEntries(
      entries
        .filter((entry) => entry.analysisError)
        .map((entry) => [entry.recordingId, entry.analysisError]),
    ) as Record<string, string>,
  };
}

async function uploadRecording(formData: FormData, timeoutMs = requestTimeoutMs) {
  return requestJson<Recording>(
    "/api/recordings/upload",
    {
      method: "POST",
      body: formData,
    },
    "上传失败。",
    timeoutMs,
  );
}

async function generateMockSegments(recordingId: string) {
  return requestJson<TranscriptSegment[]>(
    `/api/recordings/${recordingId}/segments/mock`,
    {
      method: "POST",
    },
    "生成 mock 转写失败。",
  );
}

async function transcribeRecording(recordingId: string) {
  return requestJson<TranscriptSegment[]>(
    `/api/recordings/${recordingId}/transcribe`,
    {
      method: "POST",
    },
    "真实转写失败。",
    transcribeTimeoutMs,
  );
}

async function updateSegmentText(
  recordingId: string,
  segmentId: string,
  text: string,
) {
  return requestJson<TranscriptSegment>(
    `/api/recordings/${recordingId}/segments/${segmentId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    },
    "保存转写修改失败。",
  );
}

async function updateSpeakerLabel(
  recordingId: string,
  sourceLabel: string,
  displayName: string,
) {
  return requestJson<SpeakerLabel>(
    `/api/recordings/${recordingId}/speaker-labels`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source_label: sourceLabel,
        display_name: displayName,
      }),
    },
    "保存说话人名称失败。",
  );
}

async function analyzeRecording(recordingId: string) {
  return requestJson<RecordingAnalysis>(
    `/api/recordings/${recordingId}/analyze`,
    {
      method: "POST",
    },
    "AI 总结生成失败。",
    analyzeTimeoutMs,
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatTime(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60)
    .toString()
    .padStart(2, "0");
  const remainingSeconds = (safeSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainingSeconds}`;
}

function formatRecordingDuration(milliseconds: number) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  if (hours > 0) {
    return `${hours.toString().padStart(2, "0")}:${minutes}:${seconds}`;
  }
  return `${minutes}:${seconds}`;
}

function formatRecordingFilenameDate(value: Date) {
  const year = value.getFullYear().toString();
  const month = (value.getMonth() + 1).toString().padStart(2, "0");
  const day = value.getDate().toString().padStart(2, "0");
  const hours = value.getHours().toString().padStart(2, "0");
  const minutes = value.getMinutes().toString().padStart(2, "0");
  const seconds = value.getSeconds().toString().padStart(2, "0");
  return `${year}${month}${day}-${hours}${minutes}${seconds}`;
}

function formatDurationSeconds(seconds: number | null | undefined) {
  if (typeof seconds !== "number" || Number.isNaN(seconds)) {
    return "未知时长";
  }
  return formatRecordingDuration(seconds * 1000);
}

function getLibraryDateGroup(value: string): LibraryDateGroup {
  const date = new Date(value);
  const today = new Date();
  const todayStart = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  ).getTime();
  const dateStart = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  ).getTime();
  const daysDiff = Math.floor((todayStart - dateStart) / 86_400_000);

  if (daysDiff === 0) {
    return "今天";
  }
  if (daysDiff === 1) {
    return "昨天";
  }
  if (daysDiff > 1 && daysDiff <= 6) {
    return "本周";
  }
  return "更早";
}

function statusToneClass(tone: StatusTone) {
  const classes: Record<StatusTone, string> = {
    success: "border-green-200 bg-green-50 text-green-700",
    info: "border-blue-200 bg-blue-50 text-blue-700",
    neutral: "border-gray-200 bg-gray-100 text-gray-600",
    warning: "border-orange-200 bg-orange-50 text-orange-700",
    danger: "border-red-200 bg-red-50 text-red-700",
  };
  return classes[tone];
}

function chunkStatusTone(statusValue: RecordingSessionChunkStatus): StatusTone {
  if (statusValue === "completed" || statusValue === "transcribed") {
    return "success";
  }
  if (
    statusValue === "recording" ||
    statusValue === "uploading" ||
    statusValue === "transcribing" ||
    statusValue === "summarizing"
  ) {
    return "info";
  }
  if (statusValue === "failed") {
    return "danger";
  }
  return "neutral";
}

function sessionStatusTone(statusValue: RecordingSessionStatus): StatusTone {
  if (statusValue === "completed") {
    return "success";
  }
  if (statusValue === "recording" || statusValue === "stopping") {
    return "info";
  }
  return "danger";
}

function StatusPill({
  children,
  tone,
}: {
  children: ReactNode;
  tone: StatusTone;
}) {
  return (
    <span
      className={`inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-xs font-medium ${statusToneClass(
        tone,
      )}`}
    >
      {children}
    </span>
  );
}

function ToggleSwitch({
  checked,
  disabled = false,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      aria-pressed={checked}
      className={`relative h-7 w-12 shrink-0 rounded-full transition ${
        checked ? "bg-blue-600" : "bg-gray-300"
      } ${
        disabled
          ? "cursor-not-allowed opacity-60"
          : "hover:ring-2 hover:ring-blue-100"
      }`}
      disabled={disabled}
      type="button"
      onClick={() => {
        onChange(!checked);
      }}
    >
      <span
        className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition ${
          checked ? "left-6" : "left-1"
        }`}
      />
    </button>
  );
}

function SettingGroup({
  children,
  subtitle,
  title,
}: {
  children: ReactNode;
  subtitle?: string;
  title: string;
}) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-5 py-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}
      </div>
      <div className="divide-y divide-gray-100">{children}</div>
    </section>
  );
}

function SettingRow({
  children,
  description,
  title,
}: {
  children: ReactNode;
  description: string;
  title: string;
}) {
  return (
    <div className="grid gap-3 px-5 py-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,420px)] lg:items-center">
      <div>
        <p className="font-medium">{title}</p>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
      <div className="flex flex-wrap items-center justify-start gap-2 lg:justify-end">
        {children}
      </div>
    </div>
  );
}

function getPreferredRecordingMimeType() {
  if (typeof MediaRecorder === "undefined") {
    return "";
  }
  for (const mimeType of ["audio/webm;codecs=opus", "audio/webm"]) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      return mimeType;
    }
  }
  return "";
}

function TimelineSummaryCard({
  item,
  onClick,
}: {
  item: TimelineSummaryItem;
  onClick?: () => void;
}) {
  const content = (
    <>
      <span className="block text-gray-600">
        {formatTime(item.start_time)} - {formatTime(item.end_time)}
      </span>
      <span className="mt-1 block">{item.summary}</span>
    </>
  );

  if (onClick) {
    return (
      <button
        className="w-full rounded border border-gray-200 bg-white p-3 text-left text-sm"
        type="button"
        onClick={onClick}
      >
        {content}
      </button>
    );
  }

  return (
    <div className="w-full rounded border border-gray-200 bg-white p-3 text-left text-sm">
      {content}
    </div>
  );
}

function AnalysisSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-2">
      <h5 className="font-medium">{title}</h5>
      {children}
    </section>
  );
}

function AnalysisPanel({
  analysis,
  onJump,
}: {
  analysis: RecordingAnalysis;
  onJump: (startTime: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4 rounded border border-gray-200 p-4 text-sm">
      <div>
        <h4 className="font-medium">AI 总结</h4>
        <p className="mt-1 text-gray-600">
          {analysis.provider} · {analysis.model} · {formatDate(analysis.updated_at)}
        </p>
      </div>

      {analysis.is_stale ? (
        <p className="rounded border border-amber-200 bg-amber-50 p-3 text-amber-800">
          转写内容已修改，请重新生成 AI 总结
        </p>
      ) : null}

      <AnalysisSection title="标题">
        <p className="text-gray-800">{analysis.title}</p>
      </AnalysisSection>

      <AnalysisSection title="整体总结">
        <p className="text-gray-800">{analysis.summary}</p>
      </AnalysisSection>

      <AnalysisSection title="重点信息">
        {analysis.key_points.length ? (
          <ul className="list-disc space-y-1 pl-5">
            {analysis.key_points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-600">暂无重点信息。</p>
        )}
      </AnalysisSection>

      <AnalysisSection title="时间段摘要">
        {analysis.timeline_summary.length ? (
          analysis.timeline_summary.map((item, index) => (
            <TimelineSummaryCard
              item={item}
              key={`${item.start_time}-${index}`}
              onClick={() => onJump(item.start_time)}
            />
          ))
        ) : (
          <p className="text-gray-600">暂无时间段摘要。</p>
        )}
      </AnalysisSection>

      <AnalysisSection title="备注 / 待确认信息">
        {analysis.notes.length ? (
          <ul className="list-disc space-y-1 pl-5">
            {analysis.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-600">暂无备注。</p>
        )}
      </AnalysisSection>
    </div>
  );
}

function SessionSummaryPanel({
  summary,
  isGenerating,
  error,
  exportMessage,
  onGenerate,
  onTimelineJump,
  onCopyMarkdown,
  onDownloadMarkdown,
  onDownloadText,
}: {
  summary: RecordingSessionSummary | null;
  isGenerating: boolean;
  error: string;
  exportMessage: string;
  onGenerate: () => void;
  onTimelineJump: (startTime: number) => void;
  onCopyMarkdown: () => void;
  onDownloadMarkdown: () => void;
  onDownloadText: () => void;
}) {
  return (
    <div className="flex flex-col gap-3 rounded border border-gray-200 bg-white p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h5 className="font-medium">整场总结</h5>
          {summary ? (
            <p className="mt-1 text-sm text-gray-600">
              {summary.provider} · {summary.model} · {formatDate(summary.updated_at)}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={isGenerating}
            type="button"
            onClick={onGenerate}
          >
            {isGenerating ? "生成中..." : "生成整场总结"}
          </button>
          <button
            className="rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={!summary}
            type="button"
            onClick={onCopyMarkdown}
          >
            复制 Markdown
          </button>
          <button
            className="rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={!summary}
            type="button"
            onClick={onDownloadMarkdown}
          >
            下载 Markdown
          </button>
          <button
            className="rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={!summary}
            type="button"
            onClick={onDownloadText}
          >
            下载 TXT
          </button>
        </div>
      </div>

      {isGenerating ? (
        <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
          正在生成整场总结...
        </p>
      ) : null}

      {error ? (
        <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      {exportMessage ? (
        <p className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          {exportMessage}
        </p>
      ) : null}

      {!summary ? (
        <p className="rounded border border-dashed border-gray-300 p-3 text-sm text-gray-600">
          暂无整场总结。chunks 转写后可点击生成。
        </p>
      ) : (
        <div className="flex flex-col gap-4 text-sm">
          {summary.is_stale ? (
            <p className="rounded border border-amber-200 bg-amber-50 p-3 text-amber-800">
              部分分段内容已更新，整场总结可能不是最新结果，请重新生成。
            </p>
          ) : null}

          <AnalysisSection title="标题">
            <p className="text-gray-800">{summary.title}</p>
          </AnalysisSection>

          <AnalysisSection title="整体总结">
            <p className="text-gray-800">{summary.summary}</p>
          </AnalysisSection>

          <AnalysisSection title="重点信息">
            {summary.key_points.length ? (
              <ul className="list-disc space-y-1 pl-5">
                {summary.key_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">暂无重点信息。</p>
            )}
          </AnalysisSection>

          <AnalysisSection title="时间线">
            {summary.timeline.length ? (
              <div className="flex flex-col gap-2">
                {summary.timeline.map((item, index) => (
                  <button
                    className="rounded border border-gray-200 p-3 text-left"
                    key={`${item.start_time}-${index}`}
                    type="button"
                    onClick={() => {
                      onTimelineJump(item.start_time);
                    }}
                  >
                    <span className="block text-gray-600">
                      {formatTime(item.start_time)} - {formatTime(item.end_time)} ·{" "}
                      {item.title}
                    </span>
                    <span className="mt-1 block">{item.summary}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">暂无时间线。</p>
            )}
          </AnalysisSection>

          <AnalysisSection title="分段摘要">
            {summary.chunk_summaries.length ? (
              <div className="flex flex-col gap-2">
                {summary.chunk_summaries.map((item) => (
                  <button
                    className="rounded border border-gray-200 p-3 text-left"
                    key={item.chunk_index}
                    type="button"
                    onClick={() => {
                      onTimelineJump(item.start_time);
                    }}
                  >
                    <span className="block text-gray-600">
                      Chunk {item.chunk_index} · {formatTime(item.start_time)} -{" "}
                      {formatTime(item.end_time)}
                    </span>
                    <span className="mt-1 block">{item.summary}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">暂无分段摘要。</p>
            )}
          </AnalysisSection>

          <AnalysisSection title="备注">
            {summary.notes.length ? (
              <ul className="list-disc space-y-1 pl-5">
                {summary.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">暂无备注。</p>
            )}
          </AnalysisSection>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRefs = useRef<Record<string, HTMLAudioElement | null>>({});
  const browserRecorderRef = useRef<MediaRecorder | null>(null);
  const browserRecordingStreamRef = useRef<MediaStream | null>(null);
  const browserRecordingChunksRef = useRef<BlobPart[]>([]);
  const browserRecordingTimerRef = useRef<number | null>(null);
  const browserRecordingStartedAtRef = useRef<number | null>(null);
  const browserRecordingElapsedBeforePauseRef = useRef(0);
  const discardBrowserRecordingOnStopRef = useRef(false);
  const autoAnalysisRunningRef = useRef<Record<string, boolean>>({});
  const longRecorderRef = useRef<MediaRecorder | null>(null);
  const longRecordingStreamRef = useRef<MediaStream | null>(null);
  const longRecordingTimerRef = useRef<number | null>(null);
  const longSessionStartedAtRef = useRef<number | null>(null);
  const longChunkStartOffsetRef = useRef(0);
  const longChunkIndexRef = useRef(1);
  const longChunkPromisesRef = useRef<Record<string, Promise<void>>>({});
  const chunkAnalysisRunningRef = useRef<Record<string, boolean>>({});
  const discardLongRecordingOnStopRef = useRef(false);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [segmentsByRecordingId, setSegmentsByRecordingId] = useState<
    Record<string, TranscriptSegment[]>
  >({});
  const [speakerLabelsByRecordingId, setSpeakerLabelsByRecordingId] = useState<
    Record<string, SpeakerLabel[]>
  >({});
  const [analysesByRecordingId, setAnalysesByRecordingId] = useState<
    Record<string, RecordingAnalysis>
  >({});
  const [segmentErrorsByRecordingId, setSegmentErrorsByRecordingId] = useState<
    Record<string, string>
  >({});
  const [labelErrorsByRecordingId, setLabelErrorsByRecordingId] = useState<
    Record<string, string>
  >({});
  const [analysisErrorsByRecordingId, setAnalysisErrorsByRecordingId] = useState<
    Record<string, string>
  >({});
  const [audioErrorsByRecordingId, setAudioErrorsByRecordingId] = useState<
    Record<string, string>
  >({});
  const [currentTimes, setCurrentTimes] = useState<Record<string, number>>({});
  const [isGeneratingByRecordingId, setIsGeneratingByRecordingId] = useState<
    Record<string, boolean>
  >({});
  const [isTranscribingByRecordingId, setIsTranscribingByRecordingId] = useState<
    Record<string, boolean>
  >({});
  const [isAnalyzingByRecordingId, setIsAnalyzingByRecordingId] = useState<
    Record<string, boolean>
  >({});
  const [recordingSessions, setRecordingSessions] = useState<
    RecordingSession[]
  >([]);
  const [sessionSummariesBySessionId, setSessionSummariesBySessionId] =
    useState<Record<string, RecordingSessionSummary>>({});
  const [sessionSummaryErrorsBySessionId, setSessionSummaryErrorsBySessionId] =
    useState<Record<string, string>>({});
  const [
    isGeneratingSessionSummaryBySessionId,
    setIsGeneratingSessionSummaryBySessionId,
  ] = useState<Record<string, boolean>>({});
  const [
    sessionSummaryExportMessagesBySessionId,
    setSessionSummaryExportMessagesBySessionId,
  ] = useState<Record<string, string>>({});
  const [activeLongSessionId, setActiveLongSessionId] = useState<string | null>(
    null,
  );
  const [longRecordingStatus, setLongRecordingStatus] =
    useState<LongRecordingStatus>("idle");
  const [longRecordingElapsedMs, setLongRecordingElapsedMs] = useState(0);
  const [longRecordingError, setLongRecordingError] = useState("");
  const [longChunkDurationSeconds, setLongChunkDurationSeconds] = useState(180);
  const [longCurrentChunkIndex, setLongCurrentChunkIndex] = useState(1);
  const [browserRecordingStatus, setBrowserRecordingStatus] =
    useState<BrowserRecordingStatus>("idle");
  const [browserRecordingElapsedMs, setBrowserRecordingElapsedMs] = useState(0);
  const [browserRecordingError, setBrowserRecordingError] = useState("");
  const [editingSegmentId, setEditingSegmentId] = useState<string | null>(null);
  const [segmentDraftsById, setSegmentDraftsById] = useState<
    Record<string, string>
  >({});
  const [isSavingSegmentById, setIsSavingSegmentById] = useState<
    Record<string, boolean>
  >({});
  const [speakerLabelDraftsByKey, setSpeakerLabelDraftsByKey] = useState<
    Record<string, string>
  >({});
  const [isSavingSpeakerLabelByKey, setIsSavingSpeakerLabelByKey] = useState<
    Record<string, boolean>
  >({});
  const [isAutoTranscribeEnabled, setIsAutoTranscribeEnabled] =
    useState(false);
  const [isAutoSummaryEnabled, setIsAutoSummaryEnabled] = useState(false);
  const [selectedAudioDevice, setSelectedAudioDevice] = useState("default");
  const [isMiniRecorderVisible, setIsMiniRecorderVisible] = useState(false);
  const [asrServicePreference, setAsrServicePreference] =
    useState<AsrServiceOption>("aliyun");
  const [llmServicePreference, setLlmServicePreference] =
    useState<LlmServiceOption>("dashscope");
  const [asrApiKeyPlaceholder, setAsrApiKeyPlaceholder] =
    useState("••••••••••••••••");
  const [llmApiKeyPlaceholder, setLlmApiKeyPlaceholder] =
    useState("••••••••••••••••");
  const [autoAnalysisByRecordingId, setAutoAnalysisByRecordingId] = useState<
    Record<string, AutoAnalysisState>
  >({});
  const [activePage, setActivePage] = useState<AppPage>("dashboard");
  const [selectedRecordingId, setSelectedRecordingId] = useState<string | null>(
    null,
  );
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  );
  const [librarySearch, setLibrarySearch] = useState("");
  const [libraryTypeFilter, setLibraryTypeFilter] =
    useState<LibraryTypeFilter>("all");
  const [libraryStatusFilter, setLibraryStatusFilter] =
    useState<LibraryStatusFilter>("all");
  const [recordingExportMessagesById, setRecordingExportMessagesById] =
    useState<Record<string, string>>({});
  const [runtimeEnvironment, setRuntimeEnvironment] =
    useState<RuntimeEnvironment>("Browser");
  const [tauriApiBaseUrlInfo, setTauriApiBaseUrlInfo] =
    useState<TauriApiBaseUrlInfo | null>(null);
  const [tauriRuntimeInfo, setTauriRuntimeInfo] =
    useState<TauriRuntimeInfo | null>(null);
  const [tauriBackendStatus, setTauriBackendStatus] =
    useState<TauriBackendStatus | null>(null);
  const [backendHealthStatus, setBackendHealthStatus] =
    useState<BackendHealthStatus>("checking");
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [backendHealthError, setBackendHealthError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [formError, setFormError] = useState("");
  const [listError, setListError] = useState("");
  const [settingsNotice, setSettingsNotice] = useState("");
  const effectiveApiBaseUrl = getApiBaseUrl();
  const isAutoAnalysisEnabled =
    isAutoTranscribeEnabled || isAutoSummaryEnabled;

  const loadRecordings = useCallback(async () => {
    let didFinish = false;
    const timeoutId = window.setTimeout(() => {
      if (!didFinish) {
        setIsLoading(false);
        setListError(
          "录音列表加载超时，请确认 FastAPI 已启动并且前端 API 地址正确。",
        );
      }
    }, listLoadTimeoutMs);

    setIsLoading(true);
    setListError("");
    try {
      const nextState = await fetchRecordingsWithSegments();
      setRecordings(nextState.recordings);
      setSegmentsByRecordingId(nextState.segmentsByRecordingId);
      setSpeakerLabelsByRecordingId(nextState.speakerLabelsByRecordingId);
      setSegmentErrorsByRecordingId(nextState.segmentErrorsByRecordingId);
      setLabelErrorsByRecordingId(nextState.labelErrorsByRecordingId);
      setAnalysesByRecordingId(nextState.analysesByRecordingId);
      setAnalysisErrorsByRecordingId(nextState.analysisErrorsByRecordingId);
    } catch (loadError) {
      setListError(
        loadError instanceof Error ? loadError.message : "录音列表加载失败。",
      );
    } finally {
      didFinish = true;
      window.clearTimeout(timeoutId);
      setIsLoading(false);
    }
  }, []);

  const loadRecordingSessions = useCallback(async () => {
    try {
      const sessions = await fetchRecordingSessions();
      const summaryEntries = await Promise.all(
        sessions.map(async (session) => {
          try {
            const summary = await fetchRecordingSessionSummary(session.id);
            return {
              sessionId: session.id,
              summary,
              error: "",
            };
          } catch (error) {
            return {
              sessionId: session.id,
              summary: null,
              error: getApiErrorMessage(error, "整场总结加载失败。"),
            };
          }
        }),
      );
      setRecordingSessions(sessions);
      setSessionSummariesBySessionId(
        Object.fromEntries(
          summaryEntries
            .filter((entry) => entry.summary)
            .map((entry) => [entry.sessionId, entry.summary]),
        ) as Record<string, RecordingSessionSummary>,
      );
      setSessionSummaryErrorsBySessionId(
        Object.fromEntries(
          summaryEntries
            .filter((entry) => entry.error)
            .map((entry) => [entry.sessionId, entry.error]),
        ) as Record<string, string>,
      );
      setLongRecordingError("");
    } catch (error) {
      setLongRecordingError(
        getApiErrorMessage(error, "长录音会话加载失败。"),
      );
    }
  }, []);

  const checkBackendHealth = useCallback(async () => {
    setBackendHealthStatus("checking");
    setBackendHealthError("");
    try {
      const health = await fetchBackendHealth();
      setBackendHealth(health);
      setBackendHealthStatus("connected");
    } catch (error) {
      setBackendHealth(null);
      setBackendHealthStatus("disconnected");
      setBackendHealthError(
        getApiErrorMessage(error, "后端未连接，请先启动 FastAPI 服务"),
      );
    }
  }, []);

  useEffect(() => {
    void loadRecordings();
  }, [loadRecordings]);

  useEffect(() => {
    void loadRecordingSessions();
  }, [loadRecordingSessions]);

  useEffect(() => {
    const env = detectRuntimeEnvironment();
    setRuntimeEnvironment(env);
    void checkBackendHealth();
    if (env === "Tauri") {
      void invokeTauri<TauriApiBaseUrlInfo>("get_api_base_url").then((v) => {
        if (v) setTauriApiBaseUrlInfo(v);
      });
      void invokeTauri<TauriRuntimeInfo>("get_runtime_info").then((v) => {
        if (v) setTauriRuntimeInfo(v);
      });
      void invokeTauri<TauriBackendStatus>("get_backend_status").then((v) => {
        if (v) setTauriBackendStatus(v);
      });
    }
  }, [checkBackendHealth]);

  const clearBrowserRecordingTimer = useCallback(() => {
    if (browserRecordingTimerRef.current !== null) {
      window.clearInterval(browserRecordingTimerRef.current);
      browserRecordingTimerRef.current = null;
    }
  }, []);

  const releaseBrowserRecordingStream = useCallback(() => {
    browserRecordingStreamRef.current?.getTracks().forEach((track) => {
      track.stop();
    });
    browserRecordingStreamRef.current = null;
  }, []);

  const updateBrowserRecordingElapsed = useCallback(() => {
    const startedAt = browserRecordingStartedAtRef.current;
    const elapsed =
      browserRecordingElapsedBeforePauseRef.current +
      (startedAt === null ? 0 : Date.now() - startedAt);
    setBrowserRecordingElapsedMs(elapsed);
  }, []);

  const startBrowserRecordingTimer = useCallback(() => {
    clearBrowserRecordingTimer();
    updateBrowserRecordingElapsed();
    browserRecordingTimerRef.current = window.setInterval(() => {
      updateBrowserRecordingElapsed();
    }, 500);
  }, [clearBrowserRecordingTimer, updateBrowserRecordingElapsed]);

  useEffect(() => {
    return () => {
      clearBrowserRecordingTimer();
      releaseBrowserRecordingStream();
      const recorder = browserRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        discardBrowserRecordingOnStopRef.current = true;
        recorder.stop();
      }
    };
  }, [clearBrowserRecordingTimer, releaseBrowserRecordingStream]);

  const clearLongRecordingTimer = useCallback(() => {
    if (longRecordingTimerRef.current !== null) {
      window.clearInterval(longRecordingTimerRef.current);
      longRecordingTimerRef.current = null;
    }
  }, []);

  const releaseLongRecordingStream = useCallback(() => {
    longRecordingStreamRef.current?.getTracks().forEach((track) => {
      track.stop();
    });
    longRecordingStreamRef.current = null;
  }, []);

  const updateLongRecordingElapsed = useCallback(() => {
    const startedAt = longSessionStartedAtRef.current;
    setLongRecordingElapsedMs(startedAt === null ? 0 : Date.now() - startedAt);
  }, []);

  const startLongRecordingTimer = useCallback(() => {
    clearLongRecordingTimer();
    updateLongRecordingElapsed();
    longRecordingTimerRef.current = window.setInterval(() => {
      updateLongRecordingElapsed();
    }, 500);
  }, [clearLongRecordingTimer, updateLongRecordingElapsed]);

  useEffect(() => {
    return () => {
      clearLongRecordingTimer();
      releaseLongRecordingStream();
      const recorder = longRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        discardLongRecordingOnStopRef.current = true;
        recorder.stop();
      }
    };
  }, [clearLongRecordingTimer, releaseLongRecordingStream]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (
        longRecordingStatus === "recording" ||
        longRecordingStatus === "stopping"
      ) {
        event.preventDefault();
        event.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [longRecordingStatus]);

  function speakerLabelKey(recordingId: string, sourceLabel: string) {
    return `${recordingId}::${sourceLabel}`;
  }

  function handleAutoTranscribePreferenceChange(checked: boolean) {
    setIsAutoTranscribeEnabled(checked);
    if (!checked) {
      setIsAutoSummaryEnabled(false);
    }
  }

  function handleAutoSummaryPreferenceChange(checked: boolean) {
    setIsAutoSummaryEnabled(checked);
    if (checked) {
      setIsAutoTranscribeEnabled(true);
    }
  }

  function handleAutoAnalysisPreferenceChange(checked: boolean) {
    setIsAutoTranscribeEnabled(checked);
    setIsAutoSummaryEnabled(checked);
  }

  function markAnalysisStale(recordingId: string) {
    setAnalysesByRecordingId((current) => {
      const analysis = current[recordingId];
      if (!analysis) {
        return current;
      }
      return {
        ...current,
        [recordingId]: {
          ...analysis,
          is_stale: true,
        },
      };
    });
  }

  function markSessionSummaryStale(sessionId: string) {
    setSessionSummariesBySessionId((current) => {
      const summary = current[sessionId];
      if (!summary) {
        return current;
      }
      return {
        ...current,
        [sessionId]: {
          ...summary,
          is_stale: true,
        },
      };
    });
  }

  function markSessionSummariesStaleForRecording(recordingId: string) {
    const affectedSessionIds = recordingSessions
      .filter((session) =>
        (session.chunks ?? []).some((chunk) => chunk.recording_id === recordingId),
      )
      .map((session) => session.id);
    if (affectedSessionIds.length === 0) {
      return;
    }

    setSessionSummariesBySessionId((current) => {
      let hasChanges = false;
      const next = { ...current };
      for (const sessionId of affectedSessionIds) {
        const summary = next[sessionId];
        if (summary && !summary.is_stale) {
          next[sessionId] = {
            ...summary,
            is_stale: true,
          };
          hasChanges = true;
        }
      }
      return hasChanges ? next : current;
    });
  }

  function updateSegmentInState(
    recordingId: string,
    nextSegment: TranscriptSegment,
  ) {
    setSegmentsByRecordingId((current) => ({
      ...current,
      [recordingId]: (current[recordingId] ?? []).map((segment) =>
        segment.id === nextSegment.id ? nextSegment : segment,
      ),
    }));
  }

  async function refreshSpeakerLabels(recordingId: string) {
    try {
      const labels = await fetchSpeakerLabels(recordingId);
      setSpeakerLabelsByRecordingId((current) => ({
        ...current,
        [recordingId]: labels,
      }));
      setLabelErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: "",
      }));
    } catch (error) {
      setLabelErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: getApiErrorMessage(error, "说话人名称加载失败。"),
      }));
    }
  }

  function applySpeakerLabelToSegments(
    recordingId: string,
    speakerLabel: SpeakerLabel,
  ) {
    setSegmentsByRecordingId((current) => ({
      ...current,
      [recordingId]: (current[recordingId] ?? []).map((segment) =>
        segment.speaker_label === speakerLabel.source_label
          ? {
              ...segment,
              display_speaker_label: speakerLabel.display_name,
            }
          : segment,
      ),
    }));
  }

  function upsertRecordingSession(nextSession: RecordingSession) {
    setRecordingSessions((current) => {
      const exists = current.some((session) => session.id === nextSession.id);
      if (!exists) {
        return [nextSession, ...current];
      }
      return current.map((session) =>
        session.id === nextSession.id ? nextSession : session,
      );
    });
  }

  function upsertRecordingSessionChunk(
    sessionId: string,
    nextChunk: RecordingSessionChunk,
    replaceChunkId?: string,
  ) {
    setRecordingSessions((current) =>
      current.map((session) => {
        if (session.id !== sessionId) {
          return session;
        }

        const existingChunks = session.chunks ?? [];
        const matched = existingChunks.some(
          (chunk) =>
            chunk.id === nextChunk.id ||
            (replaceChunkId !== undefined && chunk.id === replaceChunkId),
        );
        const chunks = matched
          ? existingChunks.map((chunk) =>
              chunk.id === nextChunk.id ||
              (replaceChunkId !== undefined && chunk.id === replaceChunkId)
                ? nextChunk
                : chunk,
            )
          : [...existingChunks, nextChunk];

        return {
          ...session,
          chunks: chunks.sort((first, second) => first.chunk_index - second.chunk_index),
        };
      }),
    );
  }

  function updateRecordingSessionChunkLocally(
    sessionId: string,
    chunkId: string,
    updates: Partial<RecordingSessionChunk>,
  ) {
    setRecordingSessions((current) =>
      current.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              chunks: (session.chunks ?? []).map((chunk) =>
                chunk.id === chunkId ? { ...chunk, ...updates } : chunk,
              ),
            }
          : session,
      ),
    );
  }

  function setAutoAnalysisState(
    recordingId: string,
    status: AutoAnalysisStatus,
    error = "",
  ) {
    setAutoAnalysisByRecordingId((current) => ({
      ...current,
      [recordingId]: {
        status,
        error,
      },
    }));
  }

  async function runAutoAnalysis(recordingId: string) {
    if (autoAnalysisRunningRef.current[recordingId]) {
      return;
    }

    autoAnalysisRunningRef.current[recordingId] = true;
    setMessage("自动分析已开始。");
    setAutoAnalysisState(recordingId, "uploaded");
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setAnalysisErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));

    try {
      setAutoAnalysisState(recordingId, "transcribing");
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: true,
      }));

      const segments = await transcribeRecording(recordingId);
      setSegmentsByRecordingId((current) => ({
        ...current,
        [recordingId]: segments,
      }));
      await refreshSpeakerLabels(recordingId);
      markAnalysisStale(recordingId);
      markSessionSummariesStaleForRecording(recordingId);
      setAutoAnalysisState(recordingId, "transcribed");
    } catch (error) {
      const errorMessage = getApiErrorMessage(error, "真实转写失败。");
      setAutoAnalysisState(recordingId, "failed", errorMessage);
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: errorMessage,
      }));
      delete autoAnalysisRunningRef.current[recordingId];
      return;
    } finally {
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
    }

    if (!isAutoSummaryEnabled) {
      setAutoAnalysisState(recordingId, "completed");
      setMessage("自动转写已完成。");
      delete autoAnalysisRunningRef.current[recordingId];
      return;
    }

    try {
      setAutoAnalysisState(recordingId, "summarizing");
      setIsAnalyzingByRecordingId((current) => ({
        ...current,
        [recordingId]: true,
      }));

      const analysis = await analyzeRecording(recordingId);
      setAnalysesByRecordingId((current) => ({
        ...current,
        [recordingId]: analysis,
      }));
      markSessionSummariesStaleForRecording(recordingId);
      setAutoAnalysisState(recordingId, "completed");
      setMessage("自动分析已完成。");
    } catch (error) {
      const errorMessage = getApiErrorMessage(error, "AI 总结生成失败。");
      setAutoAnalysisState(recordingId, "failed", errorMessage);
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: errorMessage,
      }));
    } finally {
      setIsAnalyzingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
      delete autoAnalysisRunningRef.current[recordingId];
    }
  }

  async function setLongChunkStatus(
    sessionId: string,
    chunk: RecordingSessionChunk,
    statusValue: RecordingSessionChunkStatus,
    errorMessage: string | null = null,
  ) {
    updateRecordingSessionChunkLocally(sessionId, chunk.id, {
      status: statusValue,
      error_message: errorMessage,
    });

    try {
      const nextChunk = await updateRecordingSessionChunkStatus(
        sessionId,
        chunk.id,
        statusValue,
        errorMessage,
      );
      upsertRecordingSessionChunk(sessionId, nextChunk);
      return nextChunk;
    } catch {
      return {
        ...chunk,
        status: statusValue,
        error_message: errorMessage,
      };
    }
  }

  async function runLongChunkAutoAnalysis(
    sessionId: string,
    initialChunk: RecordingSessionChunk,
  ) {
    if (!initialChunk.recording_id) {
      updateRecordingSessionChunkLocally(sessionId, initialChunk.id, {
        status: "failed",
        error_message: "chunk 尚未关联录音，无法分析。",
      });
      return;
    }

    if (chunkAnalysisRunningRef.current[initialChunk.id]) {
      return;
    }

    chunkAnalysisRunningRef.current[initialChunk.id] = true;
    let chunk = initialChunk;
    const recordingId = initialChunk.recording_id;
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setAnalysisErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));

    try {
      chunk = await setLongChunkStatus(sessionId, chunk, "transcribing");
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: true,
      }));
      const segments = await transcribeRecording(recordingId);
      setSegmentsByRecordingId((current) => ({
        ...current,
        [recordingId]: segments,
      }));
      await refreshSpeakerLabels(recordingId);
      markAnalysisStale(recordingId);
      markSessionSummaryStale(sessionId);
      chunk = await setLongChunkStatus(sessionId, chunk, "transcribed");
    } catch (error) {
      const errorMessage = getApiErrorMessage(error, "chunk 转写失败。");
      await setLongChunkStatus(sessionId, chunk, "failed", errorMessage);
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: errorMessage,
      }));
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
      delete chunkAnalysisRunningRef.current[initialChunk.id];
      return;
    } finally {
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
    }

    try {
      chunk = await setLongChunkStatus(sessionId, chunk, "summarizing");
      setIsAnalyzingByRecordingId((current) => ({
        ...current,
        [recordingId]: true,
      }));
      const analysis = await analyzeRecording(recordingId);
      setAnalysesByRecordingId((current) => ({
        ...current,
        [recordingId]: analysis,
      }));
      markSessionSummaryStale(sessionId);
      await setLongChunkStatus(sessionId, chunk, "completed");
    } catch (error) {
      const errorMessage = getApiErrorMessage(error, "chunk AI 总结失败。");
      await setLongChunkStatus(sessionId, chunk, "failed", errorMessage);
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: errorMessage,
      }));
    } finally {
      setIsAnalyzingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
      delete chunkAnalysisRunningRef.current[initialChunk.id];
    }
  }

  async function processLongRecordingChunk(
    sessionId: string,
    blob: Blob,
    chunkIndex: number,
    startOffsetSeconds: number,
    endOffsetSeconds: number,
    mimeType: string,
  ) {
    if (blob.size === 0) {
      return;
    }

    const tempChunkId = `pending-${sessionId}-${chunkIndex}`;
    const now = new Date().toISOString();
    const pendingChunk: RecordingSessionChunk = {
      id: tempChunkId,
      session_id: sessionId,
      recording_id: null,
      chunk_index: chunkIndex,
      start_offset_seconds: startOffsetSeconds,
      end_offset_seconds: endOffsetSeconds,
      status: "uploading",
      error_message: null,
      recording: null,
      created_at: now,
      updated_at: now,
    };
    upsertRecordingSessionChunk(sessionId, pendingChunk);

    const file = new File(
      [blob],
      `session-${sessionId}-chunk-${chunkIndex}-${formatRecordingFilenameDate(
        new Date(),
      )}.webm`,
      {
        type: mimeType || blob.type || "audio/webm",
      },
    );
    const formData = new FormData();
    formData.append("file", file);
    formData.append("chunk_index", String(chunkIndex));
    formData.append("start_offset_seconds", String(startOffsetSeconds));
    formData.append("end_offset_seconds", String(endOffsetSeconds));

    try {
      const uploadedChunk = await uploadRecordingSessionChunk(sessionId, formData);
      upsertRecordingSessionChunk(sessionId, uploadedChunk, tempChunkId);
      await loadRecordings();
      await runLongChunkAutoAnalysis(sessionId, uploadedChunk);
    } catch (error) {
      const errorMessage = getApiErrorMessage(error, "长录音分段上传失败。");
      updateRecordingSessionChunkLocally(sessionId, tempChunkId, {
        status: "failed",
        error_message: errorMessage,
      });
    }
  }

  async function finalizeLongRecordingSession(sessionId: string) {
    const pendingPromises = Object.values(longChunkPromisesRef.current);
    if (pendingPromises.length > 0) {
      await Promise.allSettled(pendingPromises);
    }

    try {
      const nextSession = await updateRecordingSessionStatus(
        sessionId,
        "completed",
      );
      upsertRecordingSession(nextSession);
      setLongRecordingStatus("completed");
      setActiveLongSessionId(null);
      setMessage("长录音会话已完成。");
      await loadRecordingSessions();
      await loadRecordings();
    } catch (error) {
      setLongRecordingStatus("failed");
      setLongRecordingError(
        getApiErrorMessage(error, "长录音会话完成状态更新失败。"),
      );
    }
  }

  async function handleStartLongRecording() {
    setMessage("");
    setLongRecordingError("");

    if (
      longRecordingStatus === "requesting" ||
      longRecordingStatus === "recording" ||
      longRecordingStatus === "stopping"
    ) {
      return;
    }

    if (
      typeof window === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setLongRecordingStatus("failed");
      setLongRecordingError(
        "当前浏览器不支持网页录音，请换用 Chrome / Edge。",
      );
      return;
    }

    setLongRecordingStatus("requesting");
    setLongRecordingElapsedMs(0);
    setLongCurrentChunkIndex(1);
    longSessionStartedAtRef.current = null;
    longChunkStartOffsetRef.current = 0;
    longChunkIndexRef.current = 1;
    longChunkPromisesRef.current = {};
    discardLongRecordingOnStopRef.current = false;

    let createdSession: RecordingSession | null = null;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const session = await createRecordingSession(longChunkDurationSeconds);
      createdSession = session;
      upsertRecordingSession(session);
      setActiveLongSessionId(session.id);

      const mimeType = getPreferredRecordingMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      longRecordingStreamRef.current = stream;
      longRecorderRef.current = recorder;

      recorder.addEventListener("dataavailable", (event) => {
        if (discardLongRecordingOnStopRef.current || event.data.size === 0) {
          return;
        }

        const startedAt = longSessionStartedAtRef.current;
        if (startedAt === null) {
          return;
        }

        const chunkIndex = longChunkIndexRef.current;
        const startOffset = longChunkStartOffsetRef.current;
        const elapsedSeconds = (Date.now() - startedAt) / 1000;
        const endOffset = Math.max(startOffset + 0.1, elapsedSeconds);
        longChunkIndexRef.current = chunkIndex + 1;
        longChunkStartOffsetRef.current = endOffset;
        setLongCurrentChunkIndex(chunkIndex + 1);

        const promise = processLongRecordingChunk(
          session.id,
          event.data,
          chunkIndex,
          startOffset,
          endOffset,
          recorder.mimeType || "audio/webm",
        );
        const promiseKey = `${session.id}-${chunkIndex}`;
        longChunkPromisesRef.current[promiseKey] = promise;
        void promise.finally(() => {
          delete longChunkPromisesRef.current[promiseKey];
        });
      });

      recorder.addEventListener("stop", () => {
        clearLongRecordingTimer();
        releaseLongRecordingStream();
        longRecorderRef.current = null;

        if (discardLongRecordingOnStopRef.current) {
          discardLongRecordingOnStopRef.current = false;
          return;
        }

        updateLongRecordingElapsed();
        void finalizeLongRecordingSession(session.id);
      });

      longSessionStartedAtRef.current = Date.now();
      recorder.start(longChunkDurationSeconds * 1000);
      setLongRecordingStatus("recording");
      startLongRecordingTimer();
    } catch (error) {
      clearLongRecordingTimer();
      releaseLongRecordingStream();
      longRecorderRef.current = null;
      longSessionStartedAtRef.current = null;
      setLongRecordingElapsedMs(0);
      setLongRecordingStatus("failed");
      setLongRecordingError(
        error instanceof DOMException
          ? "无法访问麦克风，请检查浏览器权限。"
          : getApiErrorMessage(error, "开始长录音失败。"),
      );
      if (createdSession) {
        void updateRecordingSessionStatus(createdSession.id, "failed")
          .then((nextSession) => {
            upsertRecordingSession(nextSession);
          })
          .catch(() => undefined);
      }
    }
  }

  function handleStopLongRecording() {
    const recorder = longRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return;
    }

    setLongRecordingStatus("stopping");
    clearLongRecordingTimer();
    updateLongRecordingElapsed();
    if (activeLongSessionId) {
      void updateRecordingSessionStatus(activeLongSessionId, "stopping")
        .then((nextSession) => {
          upsertRecordingSession(nextSession);
        })
        .catch((error) => {
          setLongRecordingError(
            getApiErrorMessage(error, "长录音会话停止状态更新失败。"),
          );
        });
    }
    recorder.stop();
  }

  function handleRetryLongChunkAnalysis(chunk: RecordingSessionChunk) {
    if (!chunk.recording_id) {
      updateRecordingSessionChunkLocally(chunk.session_id, chunk.id, {
        status: "failed",
        error_message: "chunk 尚未关联录音，无法重试分析。",
      });
      return;
    }

    void runLongChunkAutoAnalysis(chunk.session_id, chunk);
  }

  async function handleGenerateSessionSummary(sessionId: string) {
    setSessionSummaryErrorsBySessionId((current) => ({
      ...current,
      [sessionId]: "",
    }));
    setSessionSummaryExportMessagesBySessionId((current) => ({
      ...current,
      [sessionId]: "",
    }));
    setIsGeneratingSessionSummaryBySessionId((current) => ({
      ...current,
      [sessionId]: true,
    }));

    try {
      const summary = await generateRecordingSessionSummary(sessionId);
      setSessionSummariesBySessionId((current) => ({
        ...current,
        [sessionId]: summary,
      }));
      setMessage("整场总结已生成。");
    } catch (error) {
      setSessionSummaryErrorsBySessionId((current) => ({
        ...current,
        [sessionId]: getApiErrorMessage(error, "整场总结生成失败。"),
      }));
    } finally {
      setIsGeneratingSessionSummaryBySessionId((current) => ({
        ...current,
        [sessionId]: false,
      }));
    }
  }

  async function handleCopySessionSummaryMarkdown(sessionId: string) {
    setSessionSummaryErrorsBySessionId((current) => ({
      ...current,
      [sessionId]: "",
    }));
    setSessionSummaryExportMessagesBySessionId((current) => ({
      ...current,
      [sessionId]: "",
    }));

    try {
      const markdown = await fetchRecordingSessionExport(sessionId, "md");
      await navigator.clipboard.writeText(markdown);
      setSessionSummaryExportMessagesBySessionId((current) => ({
        ...current,
        [sessionId]: "Markdown 已复制。",
      }));
    } catch (error) {
      setSessionSummaryErrorsBySessionId((current) => ({
        ...current,
        [sessionId]: getApiErrorMessage(error, "复制 Markdown 失败。"),
      }));
    }
  }

  async function handleDownloadSessionSummary(
    session: RecordingSession,
    format: "md" | "txt",
  ) {
    setSessionSummaryErrorsBySessionId((current) => ({
      ...current,
      [session.id]: "",
    }));
    setSessionSummaryExportMessagesBySessionId((current) => ({
      ...current,
      [session.id]: "",
    }));

    try {
      const content = await fetchRecordingSessionExport(session.id, format);
      const blob = new Blob([content], {
        type: format === "md" ? "text/markdown;charset=utf-8" : "text/plain;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${session.title || "recording-session-summary"}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setSessionSummaryExportMessagesBySessionId((current) => ({
        ...current,
        [session.id]: format === "md" ? "Markdown 已下载。" : "TXT 已下载。",
      }));
    } catch (error) {
      setSessionSummaryErrorsBySessionId((current) => ({
        ...current,
        [session.id]: getApiErrorMessage(error, "下载整场总结失败。"),
      }));
    }
  }

  function buildRecordingExportContent(
    recording: Recording,
    format: "md" | "txt",
  ) {
    const analysis = analysesByRecordingId[recording.id];
    const segments = segmentsByRecordingId[recording.id] ?? [];
    const title = recording.original_filename || recording.filename;
    const separator = format === "md" ? "\n\n" : "\n\n";
    const lines: string[] = [];

    if (format === "md") {
      lines.push(`# ${title}`);
      lines.push("## 录音信息");
      lines.push(`- 上传时间：${formatDate(recording.created_at)}`);
      lines.push(`- 时长：${formatDurationSeconds(recording.duration)}`);
      lines.push(`- 状态：${recording.status}`);

      lines.push("## AI 总结");
      if (analysis) {
        lines.push(`### ${analysis.title}`);
        lines.push(analysis.summary);
        if (analysis.key_points.length) {
          lines.push("### 重点信息");
          lines.push(analysis.key_points.map((point) => `- ${point}`).join("\n"));
        }
        if (analysis.timeline_summary.length) {
          lines.push("### 时间段摘要");
          lines.push(
            analysis.timeline_summary
              .map(
                (item) =>
                  `- ${formatTime(item.start_time)}-${formatTime(
                    item.end_time,
                  )}：${item.summary}`,
              )
              .join("\n"),
          );
        }
        if (analysis.notes.length) {
          lines.push("### 备注");
          lines.push(analysis.notes.map((note) => `- ${note}`).join("\n"));
        }
      } else {
        lines.push("暂无 AI 总结。");
      }

      lines.push("## 转写");
      lines.push(
        segments.length
          ? segments
              .map(
                (segment) =>
                  `- ${formatTime(segment.start_time)}-${formatTime(
                    segment.end_time,
                  )} ${segment.display_speaker_label}：${segment.text}`,
              )
              .join("\n")
          : "暂无转写。",
      );
      return lines.join(separator);
    }

    lines.push(title);
    lines.push(`上传时间：${formatDate(recording.created_at)}`);
    lines.push(`时长：${formatDurationSeconds(recording.duration)}`);
    lines.push(`状态：${recording.status}`);
    lines.push("AI 总结");
    if (analysis) {
      lines.push(analysis.title);
      lines.push(analysis.summary);
      if (analysis.key_points.length) {
        lines.push(`重点信息：${analysis.key_points.join("；")}`);
      }
      if (analysis.notes.length) {
        lines.push(`备注：${analysis.notes.join("；")}`);
      }
    } else {
      lines.push("暂无 AI 总结。");
    }
    lines.push("转写");
    lines.push(
      segments.length
        ? segments
            .map(
              (segment) =>
                `${formatTime(segment.start_time)}-${formatTime(
                  segment.end_time,
                )} ${segment.display_speaker_label}：${segment.text}`,
            )
            .join("\n")
        : "暂无转写。",
    );
    return lines.join(separator);
  }

  function handleDownloadRecordingExport(
    recording: Recording,
    format: "md" | "txt",
  ) {
    const content = buildRecordingExportContent(recording, format);
    const blob = new Blob([content], {
      type:
        format === "md"
          ? "text/markdown;charset=utf-8"
          : "text/plain;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName = (recording.original_filename || "recording")
      .replace(/\.[^.]+$/, "")
      .replace(/[\\/:*?"<>|]/g, "-");
    link.href = url;
    link.download = `${safeName}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setRecordingExportMessagesById((current) => ({
      ...current,
      [recording.id]: format === "md" ? "Markdown 已导出。" : "TXT 已导出。",
    }));
  }

  function jumpToSessionOffset(session: RecordingSession, offsetSeconds: number) {
    const sortedChunks = [...(session.chunks ?? [])].sort(
      (first, second) => first.chunk_index - second.chunk_index,
    );
    const targetChunk = sortedChunks.find(
      (chunk) =>
        offsetSeconds >= chunk.start_offset_seconds &&
        offsetSeconds < chunk.end_offset_seconds,
    ) ?? sortedChunks.find((chunk) => offsetSeconds === chunk.end_offset_seconds);

    if (!targetChunk?.recording_id) {
      setSessionSummaryErrorsBySessionId((current) => ({
        ...current,
        [session.id]: "找不到对应 chunk 播放器，无法跳转。",
      }));
      return;
    }

    const relativeTime = Math.max(0, offsetSeconds - targetChunk.start_offset_seconds);
    void jumpToTime(targetChunk.recording_id, relativeTime);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setFormError("");
    setListError("");

    if (!selectedFile) {
      setFormError("请先选择 mp3、wav、m4a 或 webm 文件。");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsUploading(true);
    try {
      const recording = await uploadRecording(formData, uploadTimeoutMs);
      setMessage(isAutoAnalysisEnabled ? "上传成功，自动分析即将开始。" : "上传成功。");
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadRecordings();
      if (isAutoAnalysisEnabled) {
        void runAutoAnalysis(recording.id);
      }
    } catch (uploadError) {
      setFormError(
        uploadError instanceof Error ? uploadError.message : "上传失败。",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function uploadBrowserRecordingBlob(blob: Blob) {
    if (blob.size === 0) {
      setBrowserRecordingStatus("failed");
      setBrowserRecordingError("录音内容为空，请重新录制。");
      return;
    }

    setBrowserRecordingStatus("uploading");
    const filename = `browser-recording-${formatRecordingFilenameDate(
      new Date(),
    )}.webm`;
    const file = new File([blob], filename, {
      type: "audio/webm",
    });
    const formData = new FormData();
    formData.append("file", file);

    try {
      const recording = await uploadRecording(formData, uploadTimeoutMs);
      setBrowserRecordingStatus("uploaded");
      setMessage(
        isAutoAnalysisEnabled
          ? "浏览器录音已上传，自动分析即将开始。"
          : "浏览器录音已上传。",
      );
      await loadRecordings();
      if (isAutoAnalysisEnabled) {
        void runAutoAnalysis(recording.id);
      }
    } catch (error) {
      setBrowserRecordingStatus("failed");
      setBrowserRecordingError(
        error instanceof Error ? error.message : "浏览器录音上传失败。",
      );
    }
  }

  async function handleStartBrowserRecording() {
    setMessage("");
    setBrowserRecordingError("");

    if (
      browserRecordingStatus === "requesting" ||
      browserRecordingStatus === "recording" ||
      browserRecordingStatus === "paused" ||
      browserRecordingStatus === "stopping" ||
      browserRecordingStatus === "uploading"
    ) {
      return;
    }

    if (
      typeof window === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setBrowserRecordingStatus("failed");
      setBrowserRecordingError(
        "当前浏览器不支持网页录音，请换用 Chrome / Edge。",
      );
      return;
    }

    setBrowserRecordingStatus("requesting");
    setBrowserRecordingElapsedMs(0);
    browserRecordingElapsedBeforePauseRef.current = 0;
    browserRecordingStartedAtRef.current = null;
    browserRecordingChunksRef.current = [];
    discardBrowserRecordingOnStopRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getPreferredRecordingMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      browserRecordingStreamRef.current = stream;
      browserRecorderRef.current = recorder;

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          browserRecordingChunksRef.current.push(event.data);
        }
      });

      recorder.addEventListener("stop", () => {
        clearBrowserRecordingTimer();
        releaseBrowserRecordingStream();

        if (discardBrowserRecordingOnStopRef.current) {
          browserRecorderRef.current = null;
          browserRecordingChunksRef.current = [];
          discardBrowserRecordingOnStopRef.current = false;
          return;
        }

        updateBrowserRecordingElapsed();
        const blob = new Blob(browserRecordingChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        browserRecorderRef.current = null;
        browserRecordingChunksRef.current = [];
        void uploadBrowserRecordingBlob(blob);
      });

      recorder.start();
      browserRecordingStartedAtRef.current = Date.now();
      setBrowserRecordingStatus("recording");
      startBrowserRecordingTimer();
    } catch {
      clearBrowserRecordingTimer();
      releaseBrowserRecordingStream();
      browserRecorderRef.current = null;
      browserRecordingChunksRef.current = [];
      browserRecordingStartedAtRef.current = null;
      browserRecordingElapsedBeforePauseRef.current = 0;
      setBrowserRecordingElapsedMs(0);
      setBrowserRecordingStatus("failed");
      setBrowserRecordingError("无法访问麦克风，请检查浏览器权限。");
    }
  }

  function handlePauseBrowserRecording() {
    const recorder = browserRecorderRef.current;
    if (!recorder || recorder.state !== "recording") {
      return;
    }

    recorder.pause();
    if (browserRecordingStartedAtRef.current !== null) {
      browserRecordingElapsedBeforePauseRef.current +=
        Date.now() - browserRecordingStartedAtRef.current;
    }
    browserRecordingStartedAtRef.current = null;
    clearBrowserRecordingTimer();
    updateBrowserRecordingElapsed();
    setBrowserRecordingStatus("paused");
  }

  function handleResumeBrowserRecording() {
    const recorder = browserRecorderRef.current;
    if (!recorder || recorder.state !== "paused") {
      return;
    }

    recorder.resume();
    browserRecordingStartedAtRef.current = Date.now();
    setBrowserRecordingStatus("recording");
    startBrowserRecordingTimer();
  }

  function handleStopBrowserRecording() {
    const recorder = browserRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return;
    }

    if (recorder.state === "recording" && browserRecordingStartedAtRef.current !== null) {
      browserRecordingElapsedBeforePauseRef.current +=
        Date.now() - browserRecordingStartedAtRef.current;
    }
    browserRecordingStartedAtRef.current = null;
    clearBrowserRecordingTimer();
    updateBrowserRecordingElapsed();
    setBrowserRecordingStatus("stopping");
    recorder.stop();
  }

  async function handleGenerateMockSegments(recordingId: string) {
    setMessage("");
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setIsGeneratingByRecordingId((current) => ({
      ...current,
      [recordingId]: true,
    }));

    try {
      const segments = await generateMockSegments(recordingId);
      setSegmentsByRecordingId((current) => ({
        ...current,
        [recordingId]: segments,
      }));
      await refreshSpeakerLabels(recordingId);
      markAnalysisStale(recordingId);
      markSessionSummariesStaleForRecording(recordingId);
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: "",
      }));
      setMessage("mock 转写已生成。");
    } catch (generateError) {
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]:
          generateError instanceof Error
            ? generateError.message
            : "生成 mock 转写失败。",
      }));
    } finally {
      setIsGeneratingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
    }
  }

  async function handleTranscribeRecording(recordingId: string) {
    setMessage("");
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setIsTranscribingByRecordingId((current) => ({
      ...current,
      [recordingId]: true,
    }));

    try {
      const segments = await transcribeRecording(recordingId);
      setSegmentsByRecordingId((current) => ({
        ...current,
        [recordingId]: segments,
      }));
      await refreshSpeakerLabels(recordingId);
      markAnalysisStale(recordingId);
      markSessionSummariesStaleForRecording(recordingId);
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: "",
      }));
      setMessage("阿里云真实转写已完成。");
    } catch (transcribeError) {
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]:
          transcribeError instanceof Error
            ? transcribeError.message
            : "真实转写失败。",
      }));
    } finally {
      setIsTranscribingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
    }
  }

  async function handleAnalyzeRecording(recordingId: string) {
    const segments = segmentsByRecordingId[recordingId] ?? [];
    setMessage("");
    setAnalysisErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));

    if (segments.length === 0) {
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: "请先完成转写，再生成 AI 总结。",
      }));
      return;
    }

    setIsAnalyzingByRecordingId((current) => ({
      ...current,
      [recordingId]: true,
    }));

    try {
      const analysis = await analyzeRecording(recordingId);
      setAnalysesByRecordingId((current) => ({
        ...current,
        [recordingId]: analysis,
      }));
      markSessionSummariesStaleForRecording(recordingId);
      setMessage("AI 总结已生成。");
    } catch (analysisError) {
      setAnalysisErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]:
          analysisError instanceof Error
            ? analysisError.message
            : "AI 总结生成失败。",
      }));
    } finally {
      setIsAnalyzingByRecordingId((current) => ({
        ...current,
        [recordingId]: false,
      }));
    }
  }

  function handleStartEditSegment(segment: TranscriptSegment) {
    setEditingSegmentId(segment.id);
    setSegmentDraftsById((current) => ({
      ...current,
      [segment.id]: segment.text,
    }));
  }

  function handleCancelEditSegment(segmentId: string) {
    setEditingSegmentId((current) => (current === segmentId ? null : current));
    setSegmentDraftsById((current) => {
      const next = { ...current };
      delete next[segmentId];
      return next;
    });
  }

  async function handleSaveSegment(recordingId: string, segmentId: string) {
    const draft = segmentDraftsById[segmentId] ?? "";
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setIsSavingSegmentById((current) => ({
      ...current,
      [segmentId]: true,
    }));

    try {
      const segment = await updateSegmentText(recordingId, segmentId, draft);
      updateSegmentInState(recordingId, segment);
      markAnalysisStale(recordingId);
      markSessionSummariesStaleForRecording(recordingId);
      handleCancelEditSegment(segmentId);
      setMessage("转写修改已保存。");
    } catch (error) {
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]:
          error instanceof Error ? error.message : "保存转写修改失败。",
      }));
    } finally {
      setIsSavingSegmentById((current) => ({
        ...current,
        [segmentId]: false,
      }));
    }
  }

  async function handleSaveSpeakerLabel(
    recordingId: string,
    speakerLabel: SpeakerLabel,
  ) {
    const key = speakerLabelKey(recordingId, speakerLabel.source_label);
    const draft = speakerLabelDraftsByKey[key] ?? speakerLabel.display_name;
    setLabelErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    setIsSavingSpeakerLabelByKey((current) => ({
      ...current,
      [key]: true,
    }));

    try {
      const nextLabel = await updateSpeakerLabel(
        recordingId,
        speakerLabel.source_label,
        draft,
      );
      setSpeakerLabelsByRecordingId((current) => ({
        ...current,
        [recordingId]: (current[recordingId] ?? []).map((label) =>
          label.source_label === nextLabel.source_label ? nextLabel : label,
        ),
      }));
      applySpeakerLabelToSegments(recordingId, nextLabel);
      markAnalysisStale(recordingId);
      markSessionSummariesStaleForRecording(recordingId);
      setSpeakerLabelDraftsByKey((current) => ({
        ...current,
        [key]: nextLabel.display_name,
      }));
      setMessage("说话人名称已保存。");
    } catch (error) {
      setLabelErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]:
          error instanceof Error ? error.message : "保存说话人名称失败。",
      }));
    } finally {
      setIsSavingSpeakerLabelByKey((current) => ({
        ...current,
        [key]: false,
      }));
    }
  }

  async function jumpToTime(recordingId: string, startTime: number) {
    const audio = audioRefs.current[recordingId];
    setMessage("");

    if (!audio) {
      setSegmentErrorsByRecordingId((current) => ({
        ...current,
        [recordingId]: "播放器尚未准备好，请稍后再试。",
      }));
      return;
    }

    audio.currentTime = startTime;
    setCurrentTimes((current) => ({
      ...current,
      [recordingId]: startTime,
    }));

    try {
      await audio.play();
    } catch {
      setMessage("已跳转到对应时间；如果未自动播放，请手动点击播放器播放。");
    }
  }

  async function handleSegmentClick(
    recordingId: string,
    segment: TranscriptSegment,
  ) {
    setSegmentErrorsByRecordingId((current) => ({
      ...current,
      [recordingId]: "",
    }));
    await jumpToTime(recordingId, segment.start_time);
  }

  const completedSessionCount = recordingSessions.filter(
    (session) => session.status === "completed",
  ).length;
  const completedRecordingCount = recordings.filter(
    (recording) => analysesByRecordingId[recording.id],
  ).length;
  const activeSession = recordingSessions.find(
    (session) => session.id === activeLongSessionId,
  );
  const recentRecordings = recordings.slice(0, 3);
  const recentSessions = recordingSessions.slice(0, 3);
  const selectedRecording = selectedRecordingId
    ? recordings.find((recording) => recording.id === selectedRecordingId) ?? null
    : null;
  const selectedSession = selectedSessionId
    ? recordingSessions.find((session) => session.id === selectedSessionId) ??
      null
    : null;
  const activeNavigationPage: NavigationPage =
    activePage === "recordingDetail"
      ? "library"
      : activePage === "sessionDetail"
        ? "sessions"
        : activePage;
  const pageMeta: Record<AppPage, { title: string; subtitle: string }> = {
    dashboard: {
      title: "控制台",
      subtitle: "开始录制、上传音频，并快速查看最近分析结果。",
    },
    library: {
      title: "历史记录",
      subtitle: "所有录音与会话",
    },
    recordingDetail: {
      title: "录音详情",
      subtitle: "查看播放器、转写内容和 AI 总结。",
    },
    sessions: {
      title: "会话",
      subtitle: "长录音分段、分段总结与整场总结。",
    },
    sessionDetail: {
      title: "会话详情",
      subtitle: "查看分段状态、整场总结和导出。",
    },
    settings: {
      title: "设置",
      subtitle: "服务、音频、桌面端偏好",
    },
  };

  function getRecordingLibraryStatus(recording: Recording): {
    label: string;
    tone: StatusTone;
    filter: LibraryStatus;
  } {
    const autoAnalysis = autoAnalysisByRecordingId[recording.id];
    const hasError = Boolean(
      segmentErrorsByRecordingId[recording.id] ||
        analysisErrorsByRecordingId[recording.id] ||
        audioErrorsByRecordingId[recording.id],
    );
    if (hasError) {
      return { label: "失败", tone: "danger", filter: "failed" };
    }
    if (
      autoAnalysis &&
      runningAutoAnalysisStatuses.has(autoAnalysis.status)
    ) {
      return { label: "进行中", tone: "info", filter: "active" };
    }
    if (
      isTranscribingByRecordingId[recording.id] ||
      isAnalyzingByRecordingId[recording.id]
    ) {
      return { label: "进行中", tone: "info", filter: "active" };
    }
    return { label: "已完成", tone: "success", filter: "completed" };
  }

  function getSessionProgress(session: RecordingSession) {
    const chunks = session.chunks ?? [];
    const transcribedCount = chunks.filter((chunk) => {
      if (
        chunk.status === "transcribed" ||
        chunk.status === "summarizing" ||
        chunk.status === "completed"
      ) {
        return true;
      }
      return chunk.recording_id
        ? (segmentsByRecordingId[chunk.recording_id] ?? []).length > 0
        : false;
    }).length;
    const summarizedCount = chunks.filter((chunk) => {
      if (chunk.status === "completed") {
        return true;
      }
      return chunk.recording_id
        ? Boolean(analysesByRecordingId[chunk.recording_id])
        : false;
    }).length;
    const totalSeconds = chunks.reduce(
      (max, chunk) => Math.max(max, chunk.end_offset_seconds),
      0,
    );

    return {
      chunkCount: chunks.length,
      summarizedCount,
      totalSeconds,
      transcribedCount,
    };
  }

  function getSessionLibraryStatus(session: RecordingSession): {
    label: string;
    tone: StatusTone;
    filter: LibraryStatus;
  } {
    if (session.status === "completed") {
      return { label: "已完成", tone: "success", filter: "completed" };
    }
    if (session.status === "failed") {
      return { label: "失败", tone: "danger", filter: "failed" };
    }
    return { label: "进行中", tone: "info", filter: "active" };
  }

  const recordingLibraryItems: LibraryItem[] = recordings.map((recording) => {
    const segments = segmentsByRecordingId[recording.id] ?? [];
    const analysis = analysesByRecordingId[recording.id];
    const status = getRecordingLibraryStatus(recording);
    const tags = [
      segments.length ? "已转写" : "",
      analysis ? "已总结" : "",
    ].filter(Boolean);

    return {
      id: recording.id,
      kind: "recording",
      title: recording.original_filename,
      createdAt: recording.created_at,
      meta: `${formatDurationSeconds(recording.duration)} · ${formatBytes(
        recording.size_bytes,
      )}`,
      secondaryMeta: formatDate(recording.created_at),
      tags,
      statusLabel: status.label,
      statusTone: status.tone,
      statusFilter: status.filter,
    };
  });
  const sessionLibraryItems: LibraryItem[] = recordingSessions.map((session) => {
    const progress = getSessionProgress(session);
    const status = getSessionLibraryStatus(session);
    return {
      id: session.id,
      kind: "session",
      title: session.title,
      createdAt: session.created_at,
      meta: `${formatDurationSeconds(progress.totalSeconds)} · ${
        progress.chunkCount
      } 个分段`,
      secondaryMeta: `转写 ${progress.transcribedCount}/${progress.chunkCount} · 总结 ${progress.summarizedCount}/${progress.chunkCount}`,
      tags: ["长录音会话"],
      statusLabel: status.label,
      statusTone: status.tone,
      statusFilter: status.filter,
    };
  });
  const librarySearchText = librarySearch.trim().toLowerCase();
  const libraryItems = [...recordingLibraryItems, ...sessionLibraryItems]
    .filter((item) => {
      if (libraryTypeFilter !== "all" && item.kind !== libraryTypeFilter) {
        return false;
      }
      if (
        libraryStatusFilter !== "all" &&
        item.statusFilter !== libraryStatusFilter
      ) {
        return false;
      }
      if (!librarySearchText) {
        return true;
      }
      return item.title.toLowerCase().includes(librarySearchText);
    })
    .sort(
      (first, second) =>
        new Date(second.createdAt).getTime() -
        new Date(first.createdAt).getTime(),
    );
  const libraryGroups = libraryItems.reduce<Record<LibraryDateGroup, LibraryItem[]>>(
    (groups, item) => {
      groups[getLibraryDateGroup(item.createdAt)].push(item);
      return groups;
    },
    {
      今天: [],
      昨天: [],
      本周: [],
      更早: [],
    },
  );
  const sessionsToRender =
    activePage === "sessionDetail"
      ? selectedSession
        ? [selectedSession]
        : []
      : recordingSessions;
  const backendHealthTone: StatusTone =
    backendHealthStatus === "connected"
      ? "success"
      : backendHealthStatus === "checking"
        ? "info"
        : "danger";
  const backendHealthLabel =
    backendHealthStatus === "connected"
      ? "已连接"
      : backendHealthStatus === "checking"
        ? "检查中"
        : "未连接";
  const selectedChunkDurationIndex = Math.max(
    0,
    chunkDurationOptions.findIndex(
      (option) => option.value === longChunkDurationSeconds,
    ),
  );
  const canAdjustLongChunkDuration =
    longRecordingStatus !== "requesting" &&
    longRecordingStatus !== "recording" &&
    longRecordingStatus !== "stopping";

  return (
    <div className="min-h-screen bg-[#F5F6F8] text-[#0F172A]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[220px] border-r border-gray-200 bg-white px-4 py-6 lg:flex lg:flex-col">
        <div className="mb-7 flex items-center gap-3 px-2">
          <div className="h-6 w-6 rounded-full bg-gradient-to-br from-[#0F172A] to-[#2563EB]" />
          <div>
            <p className="text-lg font-bold tracking-wide">LUNARIS</p>
            <p className="text-xs text-gray-500">语音复盘控制台</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1">
          {appNavItems.map((item) => {
            const isActive = activeNavigationPage === item.key;
            return (
              <button
                className={`flex h-10 items-center gap-3 rounded-lg px-3 text-left text-sm font-medium transition ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
                key={item.key}
                type="button"
                onClick={() => {
                  setActivePage(item.key);
                  setSelectedRecordingId(null);
                  setSelectedSessionId(null);
                }}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-md text-[11px] ${
                    isActive ? "bg-blue-100" : "bg-gray-100"
                  }`}
                >
                  {item.icon}
                </span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="flex min-h-screen flex-col gap-6 px-4 py-4 lg:ml-[220px] lg:px-8 lg:py-7">
        <header className="flex flex-col gap-4 rounded-xl border border-gray-200 bg-white p-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold text-blue-700">LUNARIS WEB MVP</p>
            <h1 className="mt-1 text-2xl font-semibold">
              {pageMeta[activePage].title}
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {pageMeta[activePage].subtitle}
            </p>
          </div>
          {activePage !== "settings" ? (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="rounded-lg bg-gray-100 px-4 py-2">
              <p className="text-xs text-gray-500">录音</p>
              <p className="font-semibold">{recordings.length}</p>
            </div>
            <div className="rounded-lg bg-gray-100 px-4 py-2">
              <p className="text-xs text-gray-500">已总结</p>
              <p className="font-semibold">{completedRecordingCount}</p>
            </div>
            <div className="rounded-lg bg-gray-100 px-4 py-2">
              <p className="text-xs text-gray-500">会话</p>
              <p className="font-semibold">
                {completedSessionCount}/{recordingSessions.length}
              </p>
            </div>
          </div>
          ) : null}
        </header>

        <div className="grid grid-cols-2 gap-2 lg:hidden">
          {appNavItems.map((item) => (
            <button
              className={`rounded-lg border px-3 py-2 text-sm ${
                activeNavigationPage === item.key
                  ? "border-blue-200 bg-blue-50 text-blue-700"
                  : "border-gray-200 bg-white text-gray-600"
              }`}
              key={item.key}
              type="button"
              onClick={() => {
                setActivePage(item.key);
                setSelectedRecordingId(null);
                setSelectedSessionId(null);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>

        {activePage === "dashboard" ? (
          <>
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
              <div className="rounded-2xl bg-gradient-to-br from-[#0B1220] to-[#1E3A8A] p-7 text-white">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusPill
                    tone={
                      longRecordingStatus === "failed"
                        ? "danger"
                        : longRecordingStatus === "recording" ||
                            longRecordingStatus === "stopping"
                          ? "info"
                          : "neutral"
                    }
                  >
                    {longRecordingStatusText[longRecordingStatus]}
                  </StatusPill>
                  <span className="text-sm text-blue-100">
                    当前自动分析：{isAutoAnalysisEnabled ? "已开启" : "已关闭"}
                  </span>
                </div>
                <h2 className="mt-5 text-3xl font-semibold">开始对局录制</h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-blue-100">
                  录制完整开黑过程，自动分段上传，并复用现有 ASR 与 AI 总结流程。停止后可逐段查看转写、分段总结和整场总结。
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-[#0F172A] disabled:cursor-not-allowed disabled:bg-gray-300"
                    disabled={
                      longRecordingStatus === "requesting" ||
                      longRecordingStatus === "recording" ||
                      longRecordingStatus === "stopping"
                    }
                    type="button"
                    onClick={() => {
                      void handleStartLongRecording();
                      setActivePage("sessions");
                    }}
                  >
                    开始长录音
                  </button>
                  <button
                    className="rounded-lg border border-white/30 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:text-white/40"
                    disabled={longRecordingStatus !== "recording"}
                    type="button"
                    onClick={handleStopLongRecording}
                  >
                    停止录制
                  </button>
                  <button
                    className="rounded-lg border border-white/30 px-4 py-2 text-sm font-semibold text-white"
                    type="button"
                    onClick={() => {
                      setActivePage("library");
                    }}
                  >
                    查看历史
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-5">
                <p className="text-sm font-semibold">当前任务</p>
                <h3 className="mt-3 text-lg font-semibold">
                  {activeSession?.title ?? "暂无正在录制的长会话"}
                </h3>
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg bg-gray-100 p-3">
                    <p className="text-xs text-gray-500">总录制时长</p>
                    <p className="mt-1 font-semibold">
                      {formatRecordingDuration(longRecordingElapsedMs)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-gray-100 p-3">
                    <p className="text-xs text-gray-500">当前 chunk</p>
                    <p className="mt-1 font-semibold">第 {longCurrentChunkIndex} 段</p>
                  </div>
                </div>
                <button
                  className="mt-4 w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium"
                  type="button"
                  onClick={() => {
                    setActivePage("sessions");
                  }}
                >
                  打开会话详情
                </button>
              </div>
            </section>

            <section className="grid gap-4 xl:grid-cols-2">

      <form
        className="flex flex-col gap-4 rounded border border-gray-200 p-4"
        onSubmit={handleSubmit}
      >
        <label className="flex flex-col gap-2 text-sm font-medium">
          选择音频文件
          <input
            ref={fileInputRef}
            accept=".mp3,.wav,.m4a,.webm,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/webm"
            className="rounded border border-gray-300 p-2 font-normal"
            disabled={isUploading}
            type="file"
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] ?? null);
              setMessage("");
              setFormError("");
            }}
          />
        </label>
        <label className="flex items-start gap-3 rounded border border-gray-200 bg-gray-50 p-3 text-sm">
          <input
            checked={isAutoAnalysisEnabled}
            className="mt-1"
            type="checkbox"
            onChange={(event) => {
              handleAutoAnalysisPreferenceChange(event.target.checked);
            }}
          />
          <span>
            <span className="block font-medium">上传/录音完成后自动分析</span>
            <span className="mt-1 block text-gray-600">
              开启后会自动执行阿里云真实转写，再生成 AI 总结；关闭时保留手动流程。
            </span>
          </span>
        </label>
        <button
          className="w-fit rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-gray-400"
          disabled={isUploading}
          type="submit"
        >
          {isUploading ? "上传中..." : "上传"}
        </button>
        {message ? <p className="text-sm text-green-700">{message}</p> : null}
        {formError ? <p className="text-sm text-red-700">{formError}</p> : null}
      </form>

      <section className="flex flex-col gap-4 rounded border border-gray-200 p-4">
        <div>
          <h2 className="text-xl font-semibold">浏览器录音</h2>
          <p className="mt-1 text-sm text-gray-600">
            使用当前浏览器录制麦克风音频，停止后自动上传到录音列表。
          </p>
          <p className="mt-1 text-sm text-gray-600">
            当前自动分析：{isAutoAnalysisEnabled ? "已开启" : "已关闭"}
          </p>
        </div>

        <div className="flex flex-wrap gap-4 text-sm">
          <p>
            状态：
            <span className="font-medium">
              {browserRecordingStatusText[browserRecordingStatus]}
            </span>
          </p>
          <p>
            时长：
            <span className="font-medium">
              {formatRecordingDuration(browserRecordingElapsedMs)}
            </span>
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-gray-400"
            disabled={
              browserRecordingStatus === "requesting" ||
              browserRecordingStatus === "recording" ||
              browserRecordingStatus === "paused" ||
              browserRecordingStatus === "stopping" ||
              browserRecordingStatus === "uploading"
            }
            type="button"
            onClick={() => {
              void handleStartBrowserRecording();
            }}
          >
            开始录音
          </button>
          <button
            className="rounded border border-gray-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={browserRecordingStatus !== "recording"}
            type="button"
            onClick={handlePauseBrowserRecording}
          >
            暂停
          </button>
          <button
            className="rounded border border-gray-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={browserRecordingStatus !== "paused"}
            type="button"
            onClick={handleResumeBrowserRecording}
          >
            继续
          </button>
          <button
            className="rounded border border-gray-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
            disabled={
              browserRecordingStatus !== "recording" &&
              browserRecordingStatus !== "paused"
            }
            type="button"
            onClick={handleStopBrowserRecording}
          >
            停止并上传
          </button>
        </div>

        {browserRecordingStatus === "requesting" ? (
          <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
            正在请求麦克风权限...
          </p>
        ) : null}

        {browserRecordingStatus === "uploading" ? (
          <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
            录音已停止，正在上传...
          </p>
        ) : null}

        {browserRecordingError ? (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {browserRecordingError}
          </p>
        ) : null}
      </section>
            </section>

            <section className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">最近录音</h3>
                  <button
                    className="text-sm text-blue-700"
                    type="button"
                    onClick={() => {
                      setActivePage("library");
                    }}
                  >
                    查看全部
                  </button>
                </div>
                {recentRecordings.length ? (
                  <div className="mt-4 flex flex-col gap-2">
                    {recentRecordings.map((recording) => (
                      <button
                        className="flex items-center justify-between gap-3 rounded-lg bg-gray-100 px-3 py-2 text-left"
                        key={recording.id}
                        type="button"
                        onClick={() => {
                          setActivePage("library");
                        }}
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium">
                            {recording.original_filename}
                          </span>
                          <span className="block text-xs text-gray-500">
                            {formatDate(recording.created_at)}
                          </span>
                        </span>
                        <StatusPill tone={analysesByRecordingId[recording.id] ? "success" : "neutral"}>
                          {analysesByRecordingId[recording.id] ? "已总结" : "待处理"}
                        </StatusPill>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 rounded-lg border border-dashed border-gray-300 p-3 text-sm text-gray-500">
                    暂无录音，请先上传或录制。
                  </p>
                )}
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">最近会话</h3>
                  <button
                    className="text-sm text-blue-700"
                    type="button"
                    onClick={() => {
                      setActivePage("sessions");
                    }}
                  >
                    查看全部
                  </button>
                </div>
                {recentSessions.length ? (
                  <div className="mt-4 flex flex-col gap-2">
                    {recentSessions.map((session) => (
                      <button
                        className="flex items-center justify-between gap-3 rounded-lg bg-gray-100 px-3 py-2 text-left"
                        key={session.id}
                        type="button"
                        onClick={() => {
                          setActivePage("sessions");
                        }}
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium">
                            {session.title}
                          </span>
                          <span className="block text-xs text-gray-500">
                            {formatDate(session.started_at)} · {(session.chunks ?? []).length} chunks
                          </span>
                        </span>
                        <StatusPill tone={sessionStatusTone(session.status)}>
                          {session.status}
                        </StatusPill>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 rounded-lg border border-dashed border-gray-300 p-3 text-sm text-gray-500">
                    暂无长录音会话。
                  </p>
                )}
              </div>
            </section>
          </>
        ) : null}

        {activePage === "sessions" || activePage === "sessionDetail" ? (
      <section className="flex flex-col gap-4 rounded border border-gray-200 bg-white p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold">
              {activePage === "sessionDetail" && selectedSession
                ? selectedSession.title
                : "长录音会话"}
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              持续录制麦克风音频，按固定时长自动切片上传，并对每个 chunk 自动转写和总结。
            </p>
          </div>
          {activePage === "sessionDetail" ? (
            <button
              className="w-fit rounded border border-gray-300 px-3 py-1.5 text-sm"
              type="button"
              onClick={() => {
                setActivePage("library");
                setSelectedSessionId(null);
              }}
            >
              返回历史记录
            </button>
          ) : null}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex flex-col gap-2 text-sm font-medium">
            分段时长
            <select
              className="rounded border border-gray-300 px-3 py-2 font-normal"
              disabled={
                longRecordingStatus === "requesting" ||
                longRecordingStatus === "recording" ||
                longRecordingStatus === "stopping"
              }
              value={longChunkDurationSeconds}
              onChange={(event) => {
                setLongChunkDurationSeconds(Number(event.target.value));
              }}
            >
              {chunkDurationOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-gray-400"
              disabled={
                longRecordingStatus === "requesting" ||
                longRecordingStatus === "recording" ||
                longRecordingStatus === "stopping"
              }
              type="button"
              onClick={() => {
                void handleStartLongRecording();
              }}
            >
              开始长录音
            </button>
            <button
              className="rounded border border-gray-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
              disabled={longRecordingStatus !== "recording"}
              type="button"
              onClick={handleStopLongRecording}
            >
              停止长录音
            </button>
            <button
              className="rounded border border-gray-300 px-4 py-2 text-sm"
              type="button"
              onClick={() => {
                void loadRecordingSessions();
              }}
            >
              刷新会话
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-4 text-sm">
          <p>
            状态：
            <span className="font-medium">
              {longRecordingStatusText[longRecordingStatus]}
            </span>
          </p>
          <p>
            总时长：
            <span className="font-medium">
              {formatRecordingDuration(longRecordingElapsedMs)}
            </span>
          </p>
          <p>
            当前 chunk：
            <span className="font-medium">{longCurrentChunkIndex}</span>
          </p>
        </div>

        {longRecordingStatus === "requesting" ? (
          <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
            正在请求麦克风权限...
          </p>
        ) : null}

        {longRecordingStatus === "stopping" ? (
          <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
            正在停止长录音，并等待最后 chunk 上传和分析...
          </p>
        ) : null}

        {longRecordingError ? (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {longRecordingError}
          </p>
        ) : null}

        <div className="flex flex-col gap-3">
          <h3 className="font-medium">会话与 chunks</h3>
          {sessionsToRender.length === 0 ? (
            <p className="rounded border border-dashed border-gray-300 p-3 text-sm text-gray-600">
              {activePage === "sessionDetail"
                ? "未找到该长录音会话。"
                : "暂无长录音会话。"}
            </p>
          ) : (
            sessionsToRender.map((session) => {
              const sessionSummary =
                sessionSummariesBySessionId[session.id] ?? null;
              const sessionSummaryError =
                sessionSummaryErrorsBySessionId[session.id] ?? "";
              const isGeneratingSessionSummary = Boolean(
                isGeneratingSessionSummaryBySessionId[session.id],
              );
              const sessionSummaryExportMessage =
                sessionSummaryExportMessagesBySessionId[session.id] ?? "";

              return (
                <article
                  className="flex flex-col gap-3 rounded border border-gray-200 p-3"
                  key={session.id}
                >
                <div className="flex flex-col gap-1">
                  <h4 className="font-medium">{session.title}</h4>
                  <p className="text-sm text-gray-600">
                    分段：{session.chunk_duration_seconds} 秒 · 开始：
                    {formatDate(session.started_at)}
                  </p>
                  <StatusPill tone={sessionStatusTone(session.status)}>
                    {session.status}
                  </StatusPill>
                  {session.stopped_at ? (
                    <p className="text-sm text-gray-600">
                      停止：{formatDate(session.stopped_at)}
                    </p>
                  ) : null}
                </div>

                <SessionSummaryPanel
                  error={sessionSummaryError}
                  exportMessage={sessionSummaryExportMessage}
                  isGenerating={isGeneratingSessionSummary}
                  summary={sessionSummary}
                  onCopyMarkdown={() => {
                    void handleCopySessionSummaryMarkdown(session.id);
                  }}
                  onDownloadMarkdown={() => {
                    void handleDownloadSessionSummary(session, "md");
                  }}
                  onDownloadText={() => {
                    void handleDownloadSessionSummary(session, "txt");
                  }}
                  onGenerate={() => {
                    void handleGenerateSessionSummary(session.id);
                  }}
                  onTimelineJump={(startTime) => {
                    jumpToSessionOffset(session, startTime);
                  }}
                />

                {(session.chunks ?? []).length === 0 ? (
                  <p className="rounded border border-dashed border-gray-300 p-3 text-sm text-gray-600">
                    暂无 chunk。录音达到分段时长后会自动出现。
                  </p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {(session.chunks ?? []).map((chunk) => {
                      const recordingId = chunk.recording_id;
                      const segments = recordingId
                        ? segmentsByRecordingId[recordingId] ?? []
                        : [];
                      const analysis = recordingId
                        ? analysesByRecordingId[recordingId]
                        : undefined;
                      const chunkError =
                        chunk.error_message ||
                        (recordingId
                          ? segmentErrorsByRecordingId[recordingId] ||
                            analysisErrorsByRecordingId[recordingId] ||
                            audioErrorsByRecordingId[recordingId]
                          : "");
                      const isChunkProcessing =
                        chunk.status === "uploading" ||
                        chunk.status === "transcribing" ||
                        chunk.status === "summarizing";
                      const chunkRecordingState =
                        chunk.status === "recording" ? "录制中" : "已切片";
                      const chunkUploadState =
                        chunk.status === "uploading"
                          ? "上传中"
                          : recordingId
                            ? "已上传"
                            : chunk.status === "failed"
                              ? "失败"
                              : "等待上传";
                      const chunkTranscriptionState =
                        chunk.status === "transcribing"
                          ? "转写中"
                          : segments.length > 0 ||
                              chunk.status === "transcribed" ||
                              chunk.status === "summarizing" ||
                              chunk.status === "completed"
                            ? "已完成"
                            : chunk.status === "failed"
                              ? "失败"
                              : "等待转写";
                      const chunkSummaryState =
                        chunk.status === "summarizing"
                          ? "总结中"
                          : analysis || chunk.status === "completed"
                            ? "已完成"
                            : chunk.status === "failed" && segments.length > 0
                              ? "失败"
                              : "等待总结";

                      return (
                        <div
                          className="flex flex-col gap-3 rounded border border-gray-200 bg-gray-50 p-3"
                          key={chunk.id}
                        >
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <h5 className="font-medium">
                                Chunk {chunk.chunk_index}
                              </h5>
                              <p className="text-sm text-gray-600">
                                {formatTime(chunk.start_offset_seconds)} -{" "}
                                {formatTime(chunk.end_offset_seconds)}
                              </p>
                              <StatusPill tone={chunkStatusTone(chunk.status)}>
                                {chunkStatusText[chunk.status]}
                              </StatusPill>
                            </div>
                            <button
                              className="w-fit rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
                              disabled={!recordingId || isChunkProcessing}
                              type="button"
                              onClick={() => {
                                handleRetryLongChunkAnalysis(chunk);
                              }}
                            >
                              重试分析
                            </button>
                          </div>

                          <div className="grid gap-2 text-sm text-gray-700 sm:grid-cols-4">
                            <p className="rounded border border-gray-200 bg-white p-2">
                              录音：{chunkRecordingState}
                            </p>
                            <p className="rounded border border-gray-200 bg-white p-2">
                              上传：{chunkUploadState}
                            </p>
                            <p className="rounded border border-gray-200 bg-white p-2">
                              转写：{chunkTranscriptionState}
                            </p>
                            <p className="rounded border border-gray-200 bg-white p-2">
                              总结：{chunkSummaryState}
                            </p>
                          </div>

                          {chunkError ? (
                            <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                              {chunkError}
                            </p>
                          ) : null}

                          {recordingId ? (
                            <>
                              <audio
                                ref={(element) => {
                                  audioRefs.current[recordingId] = element;
                                }}
                                className="w-full"
                                controls
                                src={audioUrl(recordingId)}
                                onError={() => {
                                  setAudioErrorsByRecordingId((current) => ({
                                    ...current,
                                    [recordingId]:
                                      "音频文件无法加载，请确认后端服务已启动且文件仍存在。",
                                  }));
                                }}
                                onLoadedData={() => {
                                  setAudioErrorsByRecordingId((current) => ({
                                    ...current,
                                    [recordingId]: "",
                                  }));
                                }}
                                onTimeUpdate={(event) => {
                                  const nextTime = event.currentTarget.currentTime;
                                  setCurrentTimes((current) => ({
                                    ...current,
                                    [recordingId]: nextTime,
                                  }));
                                }}
                              >
                                当前浏览器不支持音频播放。
                              </audio>

                              <div className="rounded border border-gray-200 bg-white p-3">
                                <h6 className="text-sm font-medium">转写时间轴</h6>
                                {isTranscribingByRecordingId[recordingId] ? (
                                  <p className="mt-2 text-sm text-blue-700">
                                    正在转写...
                                  </p>
                                ) : null}
                                {segments.length ? (
                                  <ol className="mt-2 flex flex-col gap-2">
                                    {segments.map((segment) => {
                                      const currentTime =
                                        currentTimes[recordingId] ?? 0;
                                      const isActive =
                                        currentTime >= segment.start_time &&
                                        currentTime < segment.end_time;
                                      return (
                                        <li
                                          className={`rounded border p-2 text-sm ${
                                            isActive
                                              ? "border-blue-500 bg-blue-50"
                                              : "border-gray-200"
                                          }`}
                                          key={segment.id}
                                        >
                                          <button
                                            className="w-full text-left"
                                            type="button"
                                            onClick={() => {
                                              void handleSegmentClick(
                                                recordingId,
                                                segment,
                                              );
                                            }}
                                          >
                                            <span className="block text-gray-600">
                                              {formatTime(segment.start_time)} -{" "}
                                              {formatTime(segment.end_time)} ·{" "}
                                              {segment.display_speaker_label}
                                            </span>
                                            <span className="mt-1 block">
                                              {segment.text}
                                            </span>
                                          </button>
                                        </li>
                                      );
                                    })}
                                  </ol>
                                ) : (
                                  <p className="mt-2 text-sm text-gray-600">
                                    暂无转写。
                                  </p>
                                )}
                              </div>

                              <div className="rounded border border-gray-200 bg-white p-3">
                                <h6 className="text-sm font-medium">AI 总结</h6>
                                {isAnalyzingByRecordingId[recordingId] ? (
                                  <p className="mt-2 text-sm text-blue-700">
                                    正在生成 AI 总结...
                                  </p>
                                ) : null}
                                {analysis ? (
                                  <div className="mt-2">
                                    <AnalysisPanel
                                      analysis={analysis}
                                      onJump={(startTime) => {
                                        void jumpToTime(recordingId, startTime);
                                      }}
                                    />
                                  </div>
                                ) : (
                                  <p className="mt-2 text-sm text-gray-600">
                                    暂无 AI 总结。
                                  </p>
                                )}
                              </div>
                            </>
                          ) : (
                            <p className="text-sm text-gray-600">
                              chunk 上传成功后会显示播放器、转写和 AI 总结。
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </article>
              );
            })
          )}
        </div>
      </section>
        ) : null}

        {activePage === "library" ? (
          <section className="flex flex-col gap-4">
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">历史记录</h2>
                  <p className="mt-1 text-sm text-gray-500">所有录音与会话</p>
                </div>
                <button
                  className="w-fit rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
                  disabled={isLoading}
                  type="button"
                  onClick={() => {
                    void Promise.all([loadRecordings(), loadRecordingSessions()]);
                  }}
                >
                  刷新
                </button>
              </div>

              <div className="mt-4 grid gap-3 xl:grid-cols-[minmax(220px,1fr)_auto_auto] xl:items-center">
                <label className="flex flex-col gap-1 text-sm font-medium">
                  搜索
                  <input
                    className="h-10 rounded-lg border border-gray-300 px-3 font-normal"
                    placeholder="搜索录音或会话"
                    value={librarySearch}
                    onChange={(event) => {
                      setLibrarySearch(event.target.value);
                    }}
                  />
                </label>

                <div className="flex flex-wrap gap-2">
                  {libraryTypeOptions.map((option) => (
                    <button
                      className={`rounded-lg border px-3 py-2 text-sm ${
                        libraryTypeFilter === option.value
                          ? "border-blue-200 bg-blue-50 text-blue-700"
                          : "border-gray-200 bg-white text-gray-600"
                      }`}
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setLibraryTypeFilter(option.value);
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  {libraryStatusOptions.map((option) => (
                    <button
                      className={`rounded-lg border px-3 py-2 text-sm ${
                        libraryStatusFilter === option.value
                          ? "border-blue-200 bg-blue-50 text-blue-700"
                          : "border-gray-200 bg-white text-gray-600"
                      }`}
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setLibraryStatusFilter(option.value);
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {isLoading ? (
              <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600">
                <p>正在加载历史记录...</p>
                <p className="mt-1">当前后端地址：{effectiveApiBaseUrl}</p>
              </div>
            ) : null}

            {!isLoading && listError ? (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <p>{listError}</p>
                <p className="mt-1 text-red-600">
                  当前后端地址：{effectiveApiBaseUrl}
                </p>
              </div>
            ) : null}

            {!isLoading && !listError && libraryItems.length === 0 ? (
              <p className="rounded-xl border border-dashed border-gray-300 bg-white p-5 text-sm text-gray-600">
                暂无匹配记录，请先上传音频、录制单段音频或创建长录音会话。
              </p>
            ) : null}

            {!isLoading && !listError ? (
              <div className="flex flex-col gap-5">
                {libraryDateGroupOrder.map((group) => {
                  const groupItems = libraryGroups[group];
                  if (groupItems.length === 0) {
                    return null;
                  }

                  return (
                    <section className="flex flex-col gap-2" key={group}>
                      <h3 className="px-1 text-sm font-semibold text-gray-500">
                        {group}
                      </h3>
                      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
                        {groupItems.map((item) => (
                          <button
                            className="grid w-full gap-3 border-b border-gray-100 px-4 py-4 text-left last:border-b-0 hover:bg-gray-50 lg:grid-cols-[40px_minmax(0,1fr)_auto] lg:items-center"
                            key={`${item.kind}-${item.id}`}
                            type="button"
                            onClick={() => {
                              if (item.kind === "recording") {
                                setSelectedRecordingId(item.id);
                                setActivePage("recordingDetail");
                                return;
                              }
                              setSelectedSessionId(item.id);
                              setActivePage("sessionDetail");
                            }}
                          >
                            <span
                              className={`flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold ${
                                item.kind === "recording"
                                  ? "bg-blue-50 text-blue-700"
                                  : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {item.kind === "recording" ? "音" : "会"}
                            </span>
                            <span className="min-w-0">
                              <span className="block truncate font-medium">
                                {item.title}
                              </span>
                              <span className="mt-1 block text-sm text-gray-500">
                                {item.meta} · {item.secondaryMeta}
                              </span>
                              <span className="mt-2 flex flex-wrap gap-1.5">
                                {item.tags.length ? (
                                  item.tags.map((tag) => (
                                    <span
                                      className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                                      key={tag}
                                    >
                                      {tag}
                                    </span>
                                  ))
                                ) : (
                                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                                    待处理
                                  </span>
                                )}
                              </span>
                            </span>
                            <span className="flex items-center gap-3 lg:justify-end">
                              <StatusPill tone={item.statusTone}>
                                {item.statusLabel}
                              </StatusPill>
                              <span className="text-sm text-gray-400">进入</span>
                            </span>
                          </button>
                        ))}
                      </div>
                    </section>
                  );
                })}
              </div>
            ) : null}
          </section>
        ) : null}

        {activePage === "recordingDetail" ? (
          selectedRecording ? (
            (() => {
              const recording = selectedRecording;
              const segments = segmentsByRecordingId[recording.id] ?? [];
              const speakerLabels =
                speakerLabelsByRecordingId[recording.id] ?? [];
              const analysis = analysesByRecordingId[recording.id];
              const status = getRecordingLibraryStatus(recording);
              const autoAnalysis = autoAnalysisByRecordingId[recording.id] ?? {
                status: "idle" as AutoAnalysisStatus,
                error: "",
              };
              const isAutoAnalysisRunning = runningAutoAnalysisStatuses.has(
                autoAnalysis.status,
              );
              const durationSeconds =
                recording.duration ??
                segments.reduce(
                  (max, segment) => Math.max(max, segment.end_time),
                  0,
                );
              const currentTime = currentTimes[recording.id] ?? 0;
              const waveformProgress =
                durationSeconds > 0
                  ? Math.min(1, currentTime / durationSeconds)
                  : 0;

              return (
                <section className="flex flex-col gap-4">
                  <div className="rounded-xl border border-gray-200 bg-white p-5">
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0">
                        <button
                          className="mb-3 rounded border border-gray-300 px-3 py-1.5 text-sm"
                          type="button"
                          onClick={() => {
                            setActivePage("library");
                            setSelectedRecordingId(null);
                          }}
                        >
                          返回历史记录
                        </button>
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="max-w-4xl truncate text-xl font-semibold">
                            {recording.original_filename}
                          </h2>
                          <StatusPill tone={status.tone}>
                            {status.label}
                          </StatusPill>
                        </div>
                        <p className="mt-1 text-sm text-gray-500">
                          {formatDate(recording.created_at)} ·{" "}
                          {formatDurationSeconds(recording.duration)} ·{" "}
                          {formatBytes(recording.size_bytes)}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <button
                          className="rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
                          disabled={
                            Boolean(isTranscribingByRecordingId[recording.id]) ||
                            Boolean(isGeneratingByRecordingId[recording.id]) ||
                            isAutoAnalysisRunning
                          }
                          type="button"
                          onClick={() => {
                            void handleTranscribeRecording(recording.id);
                          }}
                        >
                          {isTranscribingByRecordingId[recording.id]
                            ? "转写中..."
                            : "重新转写"}
                        </button>
                        <button
                          className="rounded bg-black px-3 py-1.5 text-sm text-white disabled:cursor-not-allowed disabled:bg-gray-400"
                          disabled={
                            Boolean(isAnalyzingByRecordingId[recording.id]) ||
                            isAutoAnalysisRunning
                          }
                          type="button"
                          onClick={() => {
                            void handleAnalyzeRecording(recording.id);
                          }}
                        >
                          {isAnalyzingByRecordingId[recording.id]
                            ? "总结中..."
                            : "重新总结"}
                        </button>
                        <button
                          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                          type="button"
                          onClick={() => {
                            handleDownloadRecordingExport(recording, "md");
                          }}
                        >
                          导出 Markdown
                        </button>
                        <button
                          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
                          type="button"
                          onClick={() => {
                            handleDownloadRecordingExport(recording, "txt");
                          }}
                        >
                          导出 TXT
                        </button>
                      </div>
                    </div>

                    {recordingExportMessagesById[recording.id] ? (
                      <p className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                        {recordingExportMessagesById[recording.id]}
                      </p>
                    ) : null}

                    {autoAnalysis.status !== "idle" ? (
                      <div
                        className={`mt-3 rounded border p-3 text-sm ${
                          autoAnalysis.status === "failed"
                            ? "border-red-200 bg-red-50 text-red-700"
                            : autoAnalysis.status === "completed"
                              ? "border-green-200 bg-green-50 text-green-700"
                              : "border-blue-200 bg-blue-50 text-blue-700"
                        }`}
                      >
                        <p>
                          自动分析：{autoAnalysisStatusText[autoAnalysis.status]}
                        </p>
                        {autoAnalysis.error ? (
                          <p className="mt-1">{autoAnalysis.error}</p>
                        ) : null}
                      </div>
                    ) : null}
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-white p-5">
                    <div className="grid gap-4 lg:grid-cols-[minmax(260px,420px)_1fr] lg:items-center">
                      <audio
                        ref={(element) => {
                          audioRefs.current[recording.id] = element;
                        }}
                        className="w-full"
                        controls
                        src={audioUrl(recording.id)}
                        onError={() => {
                          setAudioErrorsByRecordingId((current) => ({
                            ...current,
                            [recording.id]:
                              "音频文件无法加载，请确认后端服务已启动且文件仍存在。",
                          }));
                        }}
                        onLoadedData={() => {
                          setAudioErrorsByRecordingId((current) => ({
                            ...current,
                            [recording.id]: "",
                          }));
                        }}
                        onTimeUpdate={(event) => {
                          const nextTime = event.currentTarget.currentTime;
                          setCurrentTimes((current) => ({
                            ...current,
                            [recording.id]: nextTime,
                          }));
                        }}
                      >
                        当前浏览器不支持音频播放。
                      </audio>

                      <div className="flex h-24 items-end gap-1 rounded-lg bg-gray-100 px-3 py-3">
                        {Array.from({ length: 72 }).map((_, index) => {
                          const height =
                            16 + ((index * 17 + index * index) % 48);
                          const isPassed = index / 72 <= waveformProgress;
                          return (
                            <span
                              className={`flex-1 rounded-full ${
                                isPassed ? "bg-blue-500" : "bg-gray-300"
                              }`}
                              key={index}
                              style={{ height }}
                            />
                          );
                        })}
                      </div>
                    </div>
                    {audioErrorsByRecordingId[recording.id] ? (
                      <p className="mt-3 text-sm text-red-700">
                        {audioErrorsByRecordingId[recording.id]}
                      </p>
                    ) : null}
                  </div>

                  <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
                    <section className="rounded-xl border border-gray-200 bg-white p-5">
                      <div className="flex flex-col gap-3 border-b border-gray-100 pb-4 lg:flex-row lg:items-center lg:justify-between">
                        <div>
                          <h3 className="text-lg font-semibold">转写内容</h3>
                          <p className="mt-1 text-sm text-gray-500">
                            点击片段可跳转播放器；可编辑文本并重命名说话人。
                          </p>
                        </div>
                        <button
                          className="w-fit rounded border border-gray-300 px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
                          disabled={
                            Boolean(isGeneratingByRecordingId[recording.id]) ||
                            Boolean(isTranscribingByRecordingId[recording.id]) ||
                            isAutoAnalysisRunning
                          }
                          type="button"
                          onClick={() => {
                            void handleGenerateMockSegments(recording.id);
                          }}
                        >
                          {isGeneratingByRecordingId[recording.id]
                            ? "生成中..."
                            : "生成 mock 转写"}
                        </button>
                      </div>

                      {isTranscribingByRecordingId[recording.id] ? (
                        <p className="mt-4 rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
                          正在提交阿里云转写任务，请稍候...
                        </p>
                      ) : null}

                      {segmentErrorsByRecordingId[recording.id] ? (
                        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                          {segmentErrorsByRecordingId[recording.id]}
                        </p>
                      ) : null}

                      {labelErrorsByRecordingId[recording.id] ? (
                        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                          {labelErrorsByRecordingId[recording.id]}
                        </p>
                      ) : null}

                      {speakerLabels.length ? (
                        <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
                          <h4 className="text-sm font-medium">重命名说话人</h4>
                          <div className="mt-2 flex flex-col gap-2">
                            {speakerLabels.map((speakerLabel) => {
                              const key = speakerLabelKey(
                                recording.id,
                                speakerLabel.source_label,
                              );
                              const draft =
                                speakerLabelDraftsByKey[key] ??
                                speakerLabel.display_name;

                              return (
                                <div
                                  className="flex flex-col gap-2 rounded border border-gray-200 bg-white p-2 text-sm sm:flex-row sm:items-center"
                                  key={speakerLabel.source_label}
                                >
                                  <span className="min-w-24 text-gray-600">
                                    {speakerLabel.source_label}
                                    <span className="ml-1 text-xs">
                                      ({speakerLabel.segment_count})
                                    </span>
                                  </span>
                                  <input
                                    className="min-w-0 flex-1 rounded border border-gray-300 px-2 py-1"
                                    placeholder={speakerLabel.source_label}
                                    value={draft}
                                    onChange={(event) => {
                                      setSpeakerLabelDraftsByKey((current) => ({
                                        ...current,
                                        [key]: event.target.value,
                                      }));
                                    }}
                                  />
                                  <button
                                    className="rounded border border-gray-300 px-3 py-1 disabled:cursor-not-allowed disabled:bg-gray-100"
                                    disabled={Boolean(
                                      isSavingSpeakerLabelByKey[key],
                                    )}
                                    type="button"
                                    onClick={() => {
                                      void handleSaveSpeakerLabel(
                                        recording.id,
                                        speakerLabel,
                                      );
                                    }}
                                  >
                                    {isSavingSpeakerLabelByKey[key]
                                      ? "保存中..."
                                      : "保存名称"}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}

                      {segments.length === 0 ? (
                        <p className="mt-4 rounded border border-dashed border-gray-300 p-4 text-sm text-gray-600">
                          暂无转写，请先点击重新转写或生成 mock 转写。
                        </p>
                      ) : (
                        <ol className="mt-4 flex flex-col gap-2">
                          {segments.map((segment) => {
                            const isActive =
                              currentTime >= segment.start_time &&
                              currentTime < segment.end_time;
                            const isEditing = editingSegmentId === segment.id;
                            const draft =
                              segmentDraftsById[segment.id] ?? segment.text;

                            return (
                              <li
                                className={`rounded-lg border p-3 text-sm ${
                                  isActive
                                    ? "border-blue-500 bg-blue-50"
                                    : "border-gray-200 bg-white"
                                }`}
                                key={segment.id}
                              >
                                <div className="flex items-start gap-3">
                                  <button
                                    className="min-w-0 flex-1 text-left"
                                    type="button"
                                    onClick={() => {
                                      void handleSegmentClick(recording.id, segment);
                                    }}
                                  >
                                    <span className="block text-gray-500">
                                      {formatTime(segment.start_time)} -{" "}
                                      {formatTime(segment.end_time)} ·{" "}
                                      {segment.display_speaker_label}
                                      {segment.is_edited ? (
                                        <span className="ml-2 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                                          已编辑
                                        </span>
                                      ) : null}
                                    </span>
                                    {!isEditing ? (
                                      <span className="mt-1 block leading-6 text-gray-900">
                                        {segment.text}
                                      </span>
                                    ) : null}
                                  </button>
                                  {!isEditing ? (
                                    <button
                                      className="shrink-0 rounded border border-gray-300 px-2 py-1 text-xs"
                                      type="button"
                                      onClick={() => {
                                        handleStartEditSegment(segment);
                                      }}
                                    >
                                      编辑
                                    </button>
                                  ) : null}
                                </div>

                                {isEditing ? (
                                  <div className="mt-3 flex flex-col gap-2">
                                    <textarea
                                      className="min-h-24 rounded border border-gray-300 p-2"
                                      value={draft}
                                      onChange={(event) => {
                                        setSegmentDraftsById((current) => ({
                                          ...current,
                                          [segment.id]: event.target.value,
                                        }));
                                      }}
                                    />
                                    <div className="flex gap-2">
                                      <button
                                        className="rounded bg-black px-3 py-1.5 text-white disabled:cursor-not-allowed disabled:bg-gray-400"
                                        disabled={Boolean(
                                          isSavingSegmentById[segment.id],
                                        )}
                                        type="button"
                                        onClick={() => {
                                          void handleSaveSegment(
                                            recording.id,
                                            segment.id,
                                          );
                                        }}
                                      >
                                        {isSavingSegmentById[segment.id]
                                          ? "保存中..."
                                          : "保存"}
                                      </button>
                                      <button
                                        className="rounded border border-gray-300 px-3 py-1.5"
                                        disabled={Boolean(
                                          isSavingSegmentById[segment.id],
                                        )}
                                        type="button"
                                        onClick={() => {
                                          handleCancelEditSegment(segment.id);
                                        }}
                                      >
                                        取消
                                      </button>
                                    </div>
                                  </div>
                                ) : null}
                              </li>
                            );
                          })}
                        </ol>
                      )}
                    </section>

                    <aside className="rounded-xl border border-gray-200 bg-white p-5">
                      <div className="flex items-center justify-between gap-3">
                        <h3 className="text-lg font-semibold">AI 总结</h3>
                        {analysis ? (
                          <StatusPill tone={analysis.is_stale ? "warning" : "success"}>
                            {analysis.is_stale ? "待更新" : analysis.provider}
                          </StatusPill>
                        ) : null}
                      </div>

                      {isAnalyzingByRecordingId[recording.id] ? (
                        <p className="mt-4 rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
                          正在生成 AI 总结...
                        </p>
                      ) : null}

                      {analysisErrorsByRecordingId[recording.id] ? (
                        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                          {analysisErrorsByRecordingId[recording.id]}
                        </p>
                      ) : null}

                      {analysis ? (
                        <div className="mt-4">
                          <AnalysisPanel
                            analysis={analysis}
                            onJump={(startTime) => {
                              void jumpToTime(recording.id, startTime);
                            }}
                          />
                        </div>
                      ) : (
                        <p className="mt-4 rounded border border-dashed border-gray-300 p-4 text-sm text-gray-600">
                          暂无 AI 总结，请先完成转写后点击重新总结。
                        </p>
                      )}
                    </aside>
                  </div>
                </section>
              );
            })()
          ) : (
            <section className="rounded-xl border border-gray-200 bg-white p-5">
              <p className="text-sm text-gray-600">未找到该录音。</p>
              <button
                className="mt-3 rounded border border-gray-300 px-3 py-1.5 text-sm"
                type="button"
                onClick={() => {
                  setActivePage("library");
                  setSelectedRecordingId(null);
                }}
              >
                返回历史记录
              </button>
            </section>
          )
        ) : null}

        {activePage === "settings" ? (
          <section className="flex flex-col gap-4">
            {settingsNotice ? (
              <p className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
                {settingsNotice}
              </p>
            ) : null}

            <SettingGroup
              subtitle="面向日常录音流程的偏好设置。"
              title="常用设置"
            >
              <SettingRow
                description="Web MVP 默认使用浏览器授权的麦克风输入，后续可接入真实设备枚举。"
                title="音频输入设备"
              >
                <select
                  className="h-10 min-w-56 rounded-lg border border-gray-300 bg-white px-3 text-sm"
                  value={selectedAudioDevice}
                  onChange={(event) => {
                    setSelectedAudioDevice(event.target.value);
                  }}
                >
                  <option value="default">默认麦克风（Realtek）</option>
                  <option value="browser">浏览器默认输入设备</option>
                </select>
                <StatusPill tone="neutral">UI 占位</StatusPill>
              </SettingRow>

              <SettingRow
                description="用于长录音会话自动切片；录制中不可修改。"
                title="默认分段时长"
              >
                <div className="flex h-10 items-center rounded-lg border border-gray-300 bg-white">
                  <button
                    className="h-full px-3 text-lg disabled:cursor-not-allowed disabled:text-gray-300"
                    disabled={!canAdjustLongChunkDuration}
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.max(0, selectedChunkDurationIndex - 1);
                      setLongChunkDurationSeconds(
                        chunkDurationOptions[nextIndex].value,
                      );
                    }}
                  >
                    -
                  </button>
                  <span className="min-w-28 border-x border-gray-200 px-4 text-center text-sm font-medium">
                    {chunkDurationOptions[selectedChunkDurationIndex].label}
                  </span>
                  <button
                    className="h-full px-3 text-lg disabled:cursor-not-allowed disabled:text-gray-300"
                    disabled={!canAdjustLongChunkDuration}
                    type="button"
                    onClick={() => {
                      const nextIndex = Math.min(
                        chunkDurationOptions.length - 1,
                        selectedChunkDurationIndex + 1,
                      );
                      setLongChunkDurationSeconds(
                        chunkDurationOptions[nextIndex].value,
                      );
                    }}
                  >
                    +
                  </button>
                </div>
              </SettingRow>

              <SettingRow
                description="上传或浏览器录音完成后，自动调用当前 ASR 主链路。"
                title="录制后自动转写"
              >
                <ToggleSwitch
                  checked={isAutoTranscribeEnabled}
                  onChange={handleAutoTranscribePreferenceChange}
                />
              </SettingRow>

              <SettingRow
                description="开启后会在自动转写完成后继续生成 AI 总结。"
                title="录制后自动生成 AI 总结"
              >
                <ToggleSwitch
                  checked={isAutoSummaryEnabled}
                  onChange={handleAutoSummaryPreferenceChange}
                />
              </SettingRow>

              <SettingRow
                description="当前 Web 版仅保存显示偏好；真正悬浮窗留到桌面端。"
                title="显示迷你录音窗"
              >
                <ToggleSwitch
                  checked={isMiniRecorderVisible}
                  onChange={setIsMiniRecorderVisible}
                />
                <StatusPill tone="neutral">占位</StatusPill>
              </SettingRow>
            </SettingGroup>

            <SettingGroup
              subtitle="Provider 与本地数据配置。真实密钥仍从后端 .env 读取，前端不保存密钥。"
              title="高级设置"
            >
              <SettingRow
                description="这里展示服务偏好；实际 ASR Provider 仍由后端环境变量控制。"
                title="语音识别服务"
              >
                <div className="flex overflow-hidden rounded-lg border border-gray-300 bg-white">
                  {asrServiceOptions.map((option) => (
                    <button
                      className={`border-r border-gray-200 px-3 py-2 text-sm last:border-r-0 ${
                        asrServicePreference === option.value
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-600 hover:bg-gray-50"
                      }`}
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setAsrServicePreference(option.value);
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                <StatusPill tone="neutral">按 .env 生效</StatusPill>
              </SettingRow>

              <SettingRow
                description="DASHSCOPE_API_KEY 不在前端保存；这里只显示打码状态。"
                title="语音识别 API 密钥"
              >
                <input
                  className="h-10 min-w-48 flex-1 rounded-lg border border-gray-300 px-3 text-sm"
                  type="password"
                  value={asrApiKeyPlaceholder}
                  onChange={(event) => {
                    setAsrApiKeyPlaceholder(event.target.value);
                  }}
                />
                <button
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  type="button"
                  onClick={() => {
                    setSettingsNotice("ASR 连接测试暂由后端接口实际调用时完成。");
                  }}
                >
                  测试连接
                </button>
                <StatusPill tone={listError ? "danger" : "neutral"}>
                  {listError ? "后端异常" : "待后端验证"}
                </StatusPill>
              </SettingRow>

              <SettingRow
                description="这里展示 AI 服务偏好；真实 LLM Provider 仍由后端环境变量控制。"
                title="AI 总结服务"
              >
                <div className="flex overflow-hidden rounded-lg border border-gray-300 bg-white">
                  {llmServiceOptions.map((option) => (
                    <button
                      className={`border-r border-gray-200 px-3 py-2 text-sm last:border-r-0 ${
                        llmServicePreference === option.value
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-600 hover:bg-gray-50"
                      }`}
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setLlmServicePreference(option.value);
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                <StatusPill tone="neutral">按 .env 生效</StatusPill>
              </SettingRow>

              <SettingRow
                description="DASHSCOPE_API_KEY / OPENAI_API_KEY 仍从后端环境变量读取。"
                title="AI 总结 API 密钥"
              >
                <input
                  className="h-10 min-w-48 flex-1 rounded-lg border border-gray-300 px-3 text-sm"
                  type="password"
                  value={llmApiKeyPlaceholder}
                  onChange={(event) => {
                    setLlmApiKeyPlaceholder(event.target.value);
                  }}
                />
                <button
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  type="button"
                  onClick={() => {
                    setSettingsNotice("AI 总结连接测试暂由生成总结时的后端接口完成。");
                  }}
                >
                  测试连接
                </button>
                <StatusPill tone={listError ? "danger" : "neutral"}>
                  {listError ? "后端异常" : "待后端验证"}
                </StatusPill>
              </SettingRow>

              <SettingRow
                description="音频文件与 SQLite 数据库均保存在本地项目目录。"
                title="本地存储目录"
              >
                <code className="max-w-full truncate rounded-lg bg-gray-100 px-3 py-2 text-sm">
                  backend/storage/audio · backend/storage/app.db
                </code>
                <button
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:bg-gray-100"
                  disabled
                  type="button"
                >
                  打开目录
                </button>
                <StatusPill tone="neutral">Web 版占位</StatusPill>
              </SettingRow>

              <SettingRow
                description="开发者选项。前端请求会使用这个 Base URL 访问 FastAPI。"
                title="后端 API / Base URL"
              >
                <code className="max-w-full truncate rounded-lg bg-gray-100 px-3 py-2 text-sm">
                  {effectiveApiBaseUrl}
                </code>
                <StatusPill tone={backendHealthTone}>
                  {backendHealthLabel}
                </StatusPill>
              </SettingRow>

              <SettingRow
                description="用于确认当前页面是在普通浏览器还是 Tauri WebView 中运行。"
                title="运行环境"
              >
                <StatusPill tone={runtimeEnvironment === "Tauri" ? "info" : "neutral"}>
                  {runtimeEnvironment}
                </StatusPill>
              </SettingRow>

              <SettingRow
                description={
                  runtimeEnvironment === "Tauri"
                    ? tauriApiBaseUrlInfo
                      ? `Tauri 控制面解析：${apiBaseUrlSourceLabel[tauriApiBaseUrlInfo.source]}`
                      : "正在向 Tauri 控制面查询…"
                    : "Browser 模式下使用前端默认 API Base URL，未通过 Tauri 控制面解析。"
                }
                title="API Base URL 来源"
              >
                <StatusPill tone={runtimeEnvironment === "Tauri" ? "info" : "neutral"}>
                  {runtimeEnvironment === "Tauri"
                    ? tauriApiBaseUrlInfo
                      ? apiBaseUrlSourceLabel[tauriApiBaseUrlInfo.source]
                      : "查询中"
                    : "Browser 默认"}
                </StatusPill>
              </SettingRow>

              <SettingRow
                description={
                  runtimeEnvironment === "Tauri"
                    ? tauriBackendStatus
                      ? tauriBackendStatus.note
                      : "正在向 Tauri 控制面查询后端管理模式…"
                    : "Browser 模式下不通过 Tauri 控制面管理后端。"
                }
                title="后端管理模式"
              >
                <StatusPill tone="neutral">
                  {runtimeEnvironment === "Tauri"
                    ? tauriBackendStatus?.mode ?? "查询中"
                    : "manual-dev"}
                </StatusPill>
                <StatusPill tone="neutral">占位，生产版待实现</StatusPill>
              </SettingRow>

              {runtimeEnvironment === "Tauri" && tauriRuntimeInfo ? (
                <SettingRow
                  description={`runtime=${tauriRuntimeInfo.runtime} · app=${tauriRuntimeInfo.app_version} · tauri=${tauriRuntimeInfo.tauri_version}${
                    tauriRuntimeInfo.data_dir_override
                      ? ` · LUNARIS_DATA_DIR=${tauriRuntimeInfo.data_dir_override}`
                      : ""
                  }`}
                  title="Tauri Runtime 信息"
                >
                  <StatusPill tone="info">{tauriRuntimeInfo.runtime}</StatusPill>
                  <StatusPill tone="neutral">v{tauriRuntimeInfo.app_version}</StatusPill>
                </SettingRow>
              ) : null}

              <SettingRow
                description={
                  backendHealthStatus === "disconnected"
                    ? backendHealthError ||
                      "后端未连接，请先启动 FastAPI 服务"
                    : backendHealth
                      ? `${backendHealth.service} ${backendHealth.version}`
                      : "正在检查 FastAPI 健康状态。"
                }
                title="FastAPI 状态"
              >
                <StatusPill tone={backendHealthTone}>
                  {backendHealthLabel}
                </StatusPill>
                <button
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  type="button"
                  onClick={() => {
                    void checkBackendHealth();
                  }}
                >
                  重新检查
                </button>
              </SettingRow>

              <SettingRow
                description="当前 Web MVP 不采集系统声音，不实现托盘、置顶、开机启动等桌面端能力。"
                title="隐私与桌面端能力"
              >
                <StatusPill tone="success">本地优先</StatusPill>
                <StatusPill tone="neutral">桌面端后续</StatusPill>
              </SettingRow>
            </SettingGroup>
          </section>
        ) : null}
      </main>
    </div>
  );
}
