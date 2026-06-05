use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use serde::Serialize;
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{mpsc, Arc, Mutex};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tauri::{Manager, Runtime};

#[derive(Default)]
pub struct NativeMicRecorderState(Mutex<Option<ActiveNativeMicRecording>>);

struct ActiveNativeMicRecording {
    control_sender: mpsc::Sender<RecorderControl>,
    worker_handle: JoinHandle<Result<NativeMicStoppedRecording, String>>,
    started_at: Instant,
    sample_rate: u32,
    channels: u16,
}

enum RecorderControl {
    Stop,
}

enum StartMessage {
    Started { sample_rate: u32, channels: u16 },
    Failed(String),
}

enum WriterMessage {
    Samples(Vec<i16>),
    Finish,
}

#[derive(Clone, Serialize)]
pub struct NativeMicStatus {
    state: &'static str,
    is_recording: bool,
    elapsed_seconds: f64,
    sample_rate: Option<u32>,
    channels: Option<u16>,
}

#[derive(Serialize)]
pub struct NativeMicActionResult {
    ok: bool,
    message: String,
    status: NativeMicStatus,
}

#[derive(Serialize)]
pub struct NativeMicStopResult {
    ok: bool,
    message: String,
    recording: Option<NativeMicStoppedRecording>,
    status: NativeMicStatus,
}

#[derive(Serialize)]
pub struct NativeMicStoppedRecording {
    path: String,
    filename: String,
    mime_type: &'static str,
    duration_seconds: f64,
    size_bytes: u64,
    sample_rate: u32,
    channels: u16,
}

#[derive(Serialize)]
pub struct NativeMicUploadResult {
    ok: bool,
    message: String,
    recording: Option<Value>,
}

#[tauri::command]
pub fn get_native_microphone_status(
    state: tauri::State<NativeMicRecorderState>,
) -> NativeMicStatus {
    let guard = state.0.lock().unwrap();
    status_from_active(guard.as_ref())
}

#[tauri::command]
pub fn start_native_microphone_recording<R: Runtime>(
    app: tauri::AppHandle<R>,
    state: tauri::State<NativeMicRecorderState>,
) -> NativeMicActionResult {
    let mut guard = state.0.lock().unwrap();
    if guard.is_some() {
        return NativeMicActionResult {
            ok: false,
            message: "桌面麦克风录音已在进行中。".into(),
            status: status_from_active(guard.as_ref()),
        };
    }

    let dir = match resolve_recording_dir(&app) {
        Ok(dir) => dir,
        Err(message) => {
            return NativeMicActionResult {
                ok: false,
                message,
                status: NativeMicStatus::idle(),
            };
        }
    };
    let filename = format!("desktop-mic-recording-{}.wav", unix_timestamp_seconds());
    let path = dir.join(&filename);
    let (control_sender, control_receiver) = mpsc::channel::<RecorderControl>();
    let (start_sender, start_receiver) = mpsc::channel::<StartMessage>();
    let sample_count = Arc::new(AtomicU64::new(0));
    let worker_sample_count = sample_count.clone();
    let worker_filename = filename.clone();
    let worker_handle = thread::spawn(move || {
        recorder_worker(
            path,
            worker_filename,
            worker_sample_count,
            control_receiver,
            start_sender,
        )
    });

    match start_receiver.recv_timeout(Duration::from_secs(8)) {
        Ok(StartMessage::Started {
            sample_rate,
            channels,
        }) => {
            *guard = Some(ActiveNativeMicRecording {
                control_sender,
                worker_handle,
                started_at: Instant::now(),
                sample_rate,
                channels,
            });
            NativeMicActionResult {
                ok: true,
                message: "桌面麦克风录音已开始。".into(),
                status: status_from_active(guard.as_ref()),
            }
        }
        Ok(StartMessage::Failed(message)) => {
            let _ = worker_handle.join();
            NativeMicActionResult {
                ok: false,
                message,
                status: NativeMicStatus::idle(),
            }
        }
        Err(_) => {
            let _ = control_sender.send(RecorderControl::Stop);
            let _ = worker_handle.join();
            NativeMicActionResult {
                ok: false,
                message: "启动桌面麦克风录音超时。".into(),
                status: NativeMicStatus::idle(),
            }
        }
    }
}

#[tauri::command]
pub fn stop_native_microphone_recording(
    state: tauri::State<NativeMicRecorderState>,
) -> NativeMicStopResult {
    let Some(active) = state.0.lock().unwrap().take() else {
        return NativeMicStopResult {
            ok: false,
            message: "当前没有正在进行的桌面麦克风录音。".into(),
            recording: None,
            status: NativeMicStatus::idle(),
        };
    };

    let _ = active.control_sender.send(RecorderControl::Stop);
    match active.worker_handle.join() {
        Ok(Ok(recording)) => NativeMicStopResult {
            ok: true,
            message: "桌面麦克风录音已停止。".into(),
            recording: Some(recording),
            status: NativeMicStatus::idle(),
        },
        Ok(Err(message)) => NativeMicStopResult {
            ok: false,
            message,
            recording: None,
            status: NativeMicStatus::idle(),
        },
        Err(_) => NativeMicStopResult {
            ok: false,
            message: "桌面麦克风录音线程异常退出。".into(),
            recording: None,
            status: NativeMicStatus::idle(),
        },
    }
}

#[tauri::command]
pub async fn upload_native_microphone_recording(
    api_base_url: String,
    recording_path: String,
) -> NativeMicUploadResult {
    match tauri::async_runtime::spawn_blocking(move || {
        upload_native_microphone_recording_blocking(&api_base_url, &recording_path)
    })
    .await
    {
        Ok(result) => result,
        Err(error) => NativeMicUploadResult::error(format!("上传任务异常退出：{error}")),
    }
}

impl NativeMicStatus {
    fn idle() -> Self {
        Self {
            state: "idle",
            is_recording: false,
            elapsed_seconds: 0.0,
            sample_rate: None,
            channels: None,
        }
    }
}

impl NativeMicUploadResult {
    fn error(message: String) -> Self {
        Self {
            ok: false,
            message,
            recording: None,
        }
    }
}

fn status_from_active(active: Option<&ActiveNativeMicRecording>) -> NativeMicStatus {
    match active {
        Some(active) => NativeMicStatus {
            state: "recording",
            is_recording: true,
            elapsed_seconds: active.started_at.elapsed().as_secs_f64(),
            sample_rate: Some(active.sample_rate),
            channels: Some(active.channels),
        },
        None => NativeMicStatus::idle(),
    }
}

fn recorder_worker(
    path: PathBuf,
    filename: String,
    sample_count: Arc<AtomicU64>,
    control_receiver: mpsc::Receiver<RecorderControl>,
    start_sender: mpsc::Sender<StartMessage>,
) -> Result<NativeMicStoppedRecording, String> {
    let host = cpal::default_host();
    let device = host
        .default_input_device()
        .ok_or_else(|| "找不到可用的麦克风输入设备。".to_string())?;
    let supported_config = match device.default_input_config() {
        Ok(config) => config,
        Err(error) => {
            return fail_start(
                &start_sender,
                format!("无法读取默认麦克风输入配置：{error}"),
            );
        }
    };
    let sample_rate = supported_config.sample_rate().0;
    let channels = supported_config.channels();
    let sample_format = supported_config.sample_format();
    let stream_config = supported_config.config();

    let wav_spec = hound::WavSpec {
        channels,
        sample_rate,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };
    let writer = match hound::WavWriter::create(&path, wav_spec) {
        Ok(writer) => writer,
        Err(error) => {
            return fail_start(
                &start_sender,
                format!("无法创建桌面麦克风 WAV 文件：{error}"),
            );
        }
    };
    let (writer_sender, writer_receiver) = mpsc::channel::<WriterMessage>();
    let writer_handle = thread::spawn(move || write_wav_messages(writer, writer_receiver));

    let stream = match build_input_stream(
        &device,
        &stream_config,
        sample_format,
        writer_sender.clone(),
        sample_count.clone(),
    ) {
        Ok(stream) => stream,
        Err(message) => {
            let _ = finish_writer(writer_sender, writer_handle);
            let _ = fs::remove_file(&path);
            return fail_start(&start_sender, message);
        }
    };

    if let Err(error) = stream.play() {
        let _ = finish_writer(writer_sender, writer_handle);
        let _ = fs::remove_file(&path);
        return fail_start(&start_sender, format!("无法启动麦克风录音流：{error}"));
    }

    let _ = start_sender.send(StartMessage::Started {
        sample_rate,
        channels,
    });

    let _ = control_receiver.recv();
    drop(stream);
    let writer_result = finish_writer(writer_sender, writer_handle);
    writer_result?;

    let total_samples = sample_count.load(Ordering::Relaxed);
    if total_samples == 0 {
        let _ = fs::remove_file(&path);
        return Err("录音内容为空，请重新录制。".into());
    }

    let size_bytes = fs::metadata(&path).map(|metadata| metadata.len()).unwrap_or(0);
    let duration_seconds = total_samples as f64 / (sample_rate as f64 * channels as f64);
    Ok(NativeMicStoppedRecording {
        path: path.to_string_lossy().into_owned(),
        filename,
        mime_type: "audio/wav",
        duration_seconds,
        size_bytes,
        sample_rate,
        channels,
    })
}

fn fail_start<T>(
    start_sender: &mpsc::Sender<StartMessage>,
    message: String,
) -> Result<T, String> {
    let _ = start_sender.send(StartMessage::Failed(message.clone()));
    Err(message)
}

fn resolve_recording_dir<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("无法定位桌面数据目录：{e}"))?
        .join("data")
        .join("native-mic");
    fs::create_dir_all(&dir).map_err(|e| format!("无法创建桌面录音目录：{e}"))?;
    Ok(dir)
}

fn unix_timestamp_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn write_wav_messages<W: std::io::Write + std::io::Seek>(
    mut writer: hound::WavWriter<W>,
    receiver: mpsc::Receiver<WriterMessage>,
) -> Result<(), String> {
    while let Ok(message) = receiver.recv() {
        match message {
            WriterMessage::Samples(samples) => {
                for sample in samples {
                    writer
                        .write_sample(sample)
                        .map_err(|e| format!("写入 WAV 样本失败：{e}"))?;
                }
            }
            WriterMessage::Finish => break,
        }
    }
    writer
        .finalize()
        .map_err(|e| format!("结束 WAV 文件失败：{e}"))
}

fn finish_writer(
    writer_sender: mpsc::Sender<WriterMessage>,
    writer_handle: JoinHandle<Result<(), String>>,
) -> Result<(), String> {
    let _ = writer_sender.send(WriterMessage::Finish);
    drop(writer_sender);
    match writer_handle.join() {
        Ok(result) => result,
        Err(_) => Err("WAV 写入线程异常退出。".into()),
    }
}

fn build_input_stream(
    device: &cpal::Device,
    config: &cpal::StreamConfig,
    sample_format: cpal::SampleFormat,
    sender: mpsc::Sender<WriterMessage>,
    sample_count: Arc<AtomicU64>,
) -> Result<cpal::Stream, String> {
    let err_fn = |error| eprintln!("LUNARIS native mic stream error: {error}");
    match sample_format {
        cpal::SampleFormat::F32 => device
            .build_input_stream(
                config,
                move |data: &[f32], _| {
                    let samples = data
                        .iter()
                        .map(|sample| {
                            let sample = if sample.is_finite() { *sample } else { 0.0 };
                            (sample.clamp(-1.0, 1.0) * i16::MAX as f32) as i16
                        })
                        .collect::<Vec<_>>();
                    send_samples(&sender, &sample_count, samples);
                },
                err_fn,
                None,
            )
            .map_err(|e| format!("无法创建 f32 麦克风输入流：{e}")),
        cpal::SampleFormat::I16 => device
            .build_input_stream(
                config,
                move |data: &[i16], _| {
                    send_samples(&sender, &sample_count, data.to_vec());
                },
                err_fn,
                None,
            )
            .map_err(|e| format!("无法创建 i16 麦克风输入流：{e}")),
        cpal::SampleFormat::U16 => device
            .build_input_stream(
                config,
                move |data: &[u16], _| {
                    let samples = data
                        .iter()
                        .map(|sample| (*sample as i32 - 32768) as i16)
                        .collect::<Vec<_>>();
                    send_samples(&sender, &sample_count, samples);
                },
                err_fn,
                None,
            )
            .map_err(|e| format!("无法创建 u16 麦克风输入流：{e}")),
        other => Err(format!("暂不支持当前麦克风采样格式：{other:?}")),
    }
}

fn send_samples(
    sender: &mpsc::Sender<WriterMessage>,
    sample_count: &AtomicU64,
    samples: Vec<i16>,
) {
    if samples.is_empty() {
        return;
    }
    sample_count.fetch_add(samples.len() as u64, Ordering::Relaxed);
    let _ = sender.send(WriterMessage::Samples(samples));
}

fn upload_native_microphone_recording_blocking(
    api_base_url: &str,
    recording_path: &str,
) -> NativeMicUploadResult {
    let path = PathBuf::from(recording_path);
    if !path.exists() {
        return NativeMicUploadResult::error("桌面麦克风录音文件不存在，无法上传。".into());
    }

    let filename = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("desktop-mic-recording.wav");
    let Ok(file_bytes) = fs::read(&path) else {
        return NativeMicUploadResult::error("无法读取桌面麦克风录音文件。".into());
    };
    if file_bytes.is_empty() {
        return NativeMicUploadResult::error("桌面麦克风录音文件为空，无法上传。".into());
    }

    let (body, content_type) =
        build_multipart_body("file", filename, "audio/wav", &file_bytes);
    let url = format!("{}/api/recordings/upload", api_base_url.trim_end_matches('/'));
    let response = ureq::post(&url)
        .set("Accept", "application/json")
        .set("Content-Type", &content_type)
        .timeout(Duration::from_secs(180))
        .send_bytes(&body);

    match response {
        Ok(response) => {
            let text = response.into_string().unwrap_or_default();
            match serde_json::from_str::<Value>(&text) {
                Ok(recording) => {
                    let _ = fs::remove_file(&path);
                    NativeMicUploadResult {
                        ok: true,
                        message: "桌面麦克风录音已上传。".into(),
                        recording: Some(recording),
                    }
                }
                Err(error) => NativeMicUploadResult::error(format!(
                    "上传成功但后端响应无法解析：{error}"
                )),
            }
        }
        Err(ureq::Error::Status(code, response)) => {
            let body = response.into_string().unwrap_or_default();
            NativeMicUploadResult::error(format!(
                "桌面麦克风录音上传失败（HTTP {code}）：{}",
                summarize_error_body(&body)
            ))
        }
        Err(error) => NativeMicUploadResult::error(format!(
            "桌面麦克风录音上传失败：{error}"
        )),
    }
}

fn build_multipart_body(
    field_name: &str,
    filename: &str,
    mime_type: &str,
    file_bytes: &[u8],
) -> (Vec<u8>, String) {
    let boundary = format!(
        "----LunarisNativeMic{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos()
    );
    let mut body = Vec::with_capacity(file_bytes.len() + 512);
    body.extend_from_slice(
        format!(
            "--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n"
        )
        .as_bytes(),
    );
    body.extend_from_slice(file_bytes);
    body.extend_from_slice(format!("\r\n--{boundary}--\r\n").as_bytes());
    (body, format!("multipart/form-data; boundary={boundary}"))
}

fn summarize_error_body(body: &str) -> String {
    if let Ok(value) = serde_json::from_str::<Value>(body) {
        if let Some(detail) = value.get("detail").and_then(|detail| detail.as_str()) {
            return detail.to_string();
        }
    }
    let trimmed = body.trim();
    if trimmed.is_empty() {
        return "后端未返回错误详情。".into();
    }
    trimmed.chars().take(500).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn multipart_body_uses_file_field_and_wav_type() {
        let (body, content_type) =
            build_multipart_body("file", "sample.wav", "audio/wav", b"abc");
        let body = String::from_utf8(body).expect("multipart body should be utf-8 for headers");

        assert!(content_type.starts_with("multipart/form-data; boundary="));
        assert!(body.contains("name=\"file\"; filename=\"sample.wav\""));
        assert!(body.contains("Content-Type: audio/wav"));
        assert!(body.contains("abc"));
    }

    #[test]
    fn summarize_error_body_reads_detail() {
        assert_eq!(
            summarize_error_body(r#"{"detail":"bad upload"}"#),
            "bad upload"
        );
    }
}
