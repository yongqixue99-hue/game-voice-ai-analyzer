use serde::Serialize;
use std::env;
use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

const DEFAULT_BACKEND_PORT: u16 = 8000;
const SIDECAR_NAME: &str = "lunaris-hello-backend";
const DEFAULT_SIDECAR_PORT: u16 = 8765;
const REAL_SIDECAR_NAME: &str = "lunaris-real-backend";
const DEFAULT_REAL_BACKEND_PORT: u16 = 18080;

/// Handle to the hello-backend sidecar process (fallback / experiment link).
#[derive(Default)]
struct BackendProcess(Mutex<Option<CommandChild>>);

/// Handle to the real FastAPI backend sidecar process.
#[derive(Default)]
struct RealBackendProcess(Mutex<Option<CommandChild>>);

#[derive(Serialize)]
struct ApiBaseUrl {
    url: String,
    source: &'static str,
}

#[derive(Serialize)]
struct RuntimeInfo {
    runtime: &'static str,
    tauri_version: &'static str,
    app_version: &'static str,
    backend_management_mode: &'static str,
    data_dir_override: Option<String>,
}

#[derive(Serialize)]
struct BackendStatus {
    mode: &'static str,
    running: bool,
    pid: Option<u32>,
    api_base_url: String,
    note: &'static str,
}

#[derive(Serialize)]
struct BackendActionResult {
    ok: bool,
    mode: &'static str,
    message: String,
}

/// Port the hello sidecar binds to. Honors LUNARIS_PORT, else falls back to 8765.
fn sidecar_port() -> u16 {
    env::var("LUNARIS_PORT")
        .ok()
        .and_then(|p| p.trim().parse::<u16>().ok())
        .unwrap_or(DEFAULT_SIDECAR_PORT)
}

/// Port the real backend sidecar binds to. Honors LUNARIS_REAL_PORT, else 18080.
fn real_backend_port() -> u16 {
    env::var("LUNARIS_REAL_PORT")
        .ok()
        .and_then(|p| p.trim().parse::<u16>().ok())
        .unwrap_or(DEFAULT_REAL_BACKEND_PORT)
}

/// Data dir handed to the real backend. Uses LUNARIS_DATA_DIR when set, else the
/// OS app-data dir — frozen backends must not write to the temp extraction dir.
fn resolve_real_data_dir<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Option<String> {
    if let Ok(dir) = env::var("LUNARIS_DATA_DIR") {
        if !dir.trim().is_empty() {
            return Some(dir);
        }
    }
    app.path()
        .app_data_dir()
        .ok()
        .map(|p| p.join("data").to_string_lossy().into_owned())
}

fn resolve_api_base_url() -> ApiBaseUrl {
    if let Ok(url) = env::var("LUNARIS_API_BASE_URL") {
        if !url.trim().is_empty() {
            return ApiBaseUrl { url, source: "env:LUNARIS_API_BASE_URL" };
        }
    }
    if let Ok(port) = env::var("LUNARIS_PORT") {
        if let Ok(port) = port.trim().parse::<u16>() {
            return ApiBaseUrl {
                url: format!("http://127.0.0.1:{port}"),
                source: "env:LUNARIS_PORT",
            };
        }
    }
    ApiBaseUrl {
        url: format!("http://127.0.0.1:{DEFAULT_BACKEND_PORT}"),
        source: "default",
    }
}

/// Spawn a sidecar by name, draining its event channel so it never blocks on IO.
fn spawn_sidecar<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    sidecar_name: &str,
    port: u16,
    data_dir: Option<String>,
) -> Result<CommandChild, String> {
    let mut command = app
        .shell()
        .sidecar(sidecar_name)
        .map_err(|e| format!("无法定位 sidecar：{e}"))?
        .env("LUNARIS_PORT", port.to_string())
        .env("LUNARIS_HOST", "127.0.0.1");
    if let Some(dir) = data_dir {
        if !dir.trim().is_empty() {
            command = command.env("LUNARIS_DATA_DIR", dir);
        }
    }
    let (mut rx, child) = command.spawn().map_err(|e| format!("启动失败：{e}"))?;
    tauri::async_runtime::spawn(async move { while rx.recv().await.is_some() {} });
    Ok(child)
}

#[tauri::command]
fn get_api_base_url() -> ApiBaseUrl {
    resolve_api_base_url()
}

#[tauri::command]
fn get_runtime_info() -> RuntimeInfo {
    RuntimeInfo {
        runtime: "tauri",
        tauri_version: env!("CARGO_PKG_VERSION"),
        app_version: env!("CARGO_PKG_VERSION"),
        backend_management_mode: "sidecar",
        data_dir_override: env::var("LUNARIS_DATA_DIR").ok(),
    }
}

#[tauri::command]
fn get_backend_status(state: tauri::State<BackendProcess>) -> BackendStatus {
    let guard = state.0.lock().unwrap();
    match guard.as_ref() {
        Some(child) => BackendStatus {
            mode: "sidecar",
            running: true,
            pid: Some(child.pid()),
            api_base_url: format!("http://127.0.0.1:{}", sidecar_port()),
            note: "Tauri 通过 sidecar 管理 hello-backend 进程。",
        },
        None => BackendStatus {
            mode: "stopped",
            running: false,
            pid: None,
            api_base_url: resolve_api_base_url().url,
            note: "后端未由 Tauri 启动（外部 dev 模式或尚未启动）。",
        },
    }
}

#[tauri::command]
fn start_backend<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: tauri::State<BackendProcess>,
) -> BackendActionResult {
    let mut guard = state.0.lock().unwrap();
    if guard.is_some() {
        return BackendActionResult { ok: true, mode: "sidecar", message: "后端已在运行。".into() };
    }
    let port = sidecar_port();
    match spawn_sidecar(&app, SIDECAR_NAME, port, None) {
        Ok(child) => {
            *guard = Some(child);
            BackendActionResult {
                ok: true,
                mode: "sidecar",
                message: format!("已启动 hello-backend，端口 {port}。"),
            }
        }
        Err(message) => BackendActionResult { ok: false, mode: "sidecar", message },
    }
}

#[tauri::command]
fn stop_backend(state: tauri::State<BackendProcess>) -> BackendActionResult {
    stop_slot(&state.0)
}

#[tauri::command]
fn get_real_backend_status(state: tauri::State<RealBackendProcess>) -> BackendStatus {
    let guard = state.0.lock().unwrap();
    let port = real_backend_port();
    match guard.as_ref() {
        Some(child) => BackendStatus {
            mode: "sidecar",
            running: true,
            pid: Some(child.pid()),
            api_base_url: format!("http://127.0.0.1:{port}"),
            note: "Tauri 通过 sidecar 管理真实 FastAPI 后端。",
        },
        None => BackendStatus {
            mode: "stopped",
            running: false,
            pid: None,
            api_base_url: format!("http://127.0.0.1:{port}"),
            note: "真实后端未由 Tauri 启动。",
        },
    }
}

#[tauri::command]
fn start_real_backend<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: tauri::State<RealBackendProcess>,
) -> BackendActionResult {
    let mut guard = state.0.lock().unwrap();
    if guard.is_some() {
        return BackendActionResult { ok: true, mode: "sidecar", message: "真实后端已在运行。".into() };
    }
    let port = real_backend_port();
    let data_dir = resolve_real_data_dir(&app);
    match spawn_sidecar(&app, REAL_SIDECAR_NAME, port, data_dir) {
        Ok(child) => {
            *guard = Some(child);
            BackendActionResult {
                ok: true,
                mode: "sidecar",
                message: format!("已启动真实后端，端口 {port}。"),
            }
        }
        Err(message) => BackendActionResult { ok: false, mode: "sidecar", message },
    }
}

#[tauri::command]
fn stop_real_backend(state: tauri::State<RealBackendProcess>) -> BackendActionResult {
    stop_slot(&state.0)
}

/// Take and terminate whatever child is held in a process slot.
fn stop_slot(slot: &Mutex<Option<CommandChild>>) -> BackendActionResult {
    let mut guard = slot.lock().unwrap();
    let Some(child) = guard.take() else {
        return BackendActionResult { ok: true, mode: "stopped", message: "后端未在运行。".into() };
    };
    match terminate_backend(child.pid(), child) {
        Ok(()) => BackendActionResult { ok: true, mode: "stopped", message: "已停止后端。".into() },
        Err(e) => BackendActionResult { ok: false, mode: "sidecar", message: format!("停止失败：{e}") },
    }
}

/// Best-effort terminate on app exit; second call on an empty slot is a no-op.
fn terminate_slot(slot: &Mutex<Option<CommandChild>>) {
    if let Some(child) = slot.lock().unwrap().take() {
        let _ = terminate_backend(child.pid(), child);
    }
}

/// Stop the sidecar. The PyInstaller onefile bootloader forks a server child;
/// SIGKILL (CommandChild::kill) would orphan that child and leak the port, so on
/// unix we send SIGTERM to the bootloader, which forwards it for a graceful exit.
#[cfg(unix)]
fn terminate_backend(
    pid: u32,
    _child: tauri_plugin_shell::process::CommandChild,
) -> std::io::Result<()> {
    let status = std::process::Command::new("kill")
        .args(["-TERM", &pid.to_string()])
        .status()?;
    if status.success() {
        Ok(())
    } else {
        Err(std::io::Error::other(format!("kill -TERM {pid} -> {status}")))
    }
}

#[cfg(not(unix))]
fn terminate_backend(
    _pid: u32,
    child: tauri_plugin_shell::process::CommandChild,
) -> std::io::Result<()> {
    child.kill().map_err(|e| std::io::Error::other(e.to_string()))
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess::default())
        .manage(RealBackendProcess::default())
        .setup(|app| {
            let result = start_real_backend(app.handle().clone(), app.state());
            if !result.ok {
                eprintln!("LUNARIS real backend auto-start failed: {}", result.message);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_api_base_url,
            get_runtime_info,
            get_backend_status,
            start_backend,
            stop_backend,
            get_real_backend_status,
            start_real_backend,
            stop_real_backend,
        ])
        .build(tauri::generate_context!())
        .expect("error while running LUNARIS Tauri shell")
        .run(|app_handle, event| {
            // On exit, stop any sidecars Tauri started so they don't leak ports.
            if matches!(event, tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit) {
                terminate_slot(&app_handle.state::<BackendProcess>().0);
                terminate_slot(&app_handle.state::<RealBackendProcess>().0);
            }
        });
}

#[cfg(test)]
mod sidecar_tests {
    use super::*;
    use std::path::PathBuf;
    use std::process::Command as StdCommand;
    use std::time::Duration;
    use tauri::Manager;

    /// plugin-shell resolves a sidecar relative to the current exe; under
    /// `cargo test` that's target/debug/deps/, so stage the verified binary there.
    fn stage_sidecar(triple_name: &str, link_name: &str) {
        let src = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("binaries")
            .join(triple_name);
        let exe_dir = std::env::current_exe().unwrap().parent().unwrap().to_path_buf();
        std::fs::copy(&src, exe_dir.join(link_name)).expect("stage sidecar");
    }

    fn curl_health(port: u16) -> Option<String> {
        let out = StdCommand::new("curl")
            .args(["-s", "-m", "3", &format!("http://127.0.0.1:{port}/api/health")])
            .output()
            .ok()?;
        let body = String::from_utf8_lossy(&out.stdout).to_string();
        (!body.trim().is_empty()).then_some(body)
    }

    fn poll_health(port: u16, attempts: u32) -> Option<String> {
        for _ in 0..attempts {
            std::thread::sleep(Duration::from_millis(800));
            if let Some(body) = curl_health(port) {
                return Some(body);
            }
        }
        None
    }

    fn wait_port_freed(port: u16) -> bool {
        for _ in 0..10 {
            std::thread::sleep(Duration::from_millis(500));
            if curl_health(port).is_none() {
                return true;
            }
        }
        false
    }

    #[test]
    fn hello_sidecar_spawn_health_kill() {
        const PORT: u16 = 8799;
        stage_sidecar("lunaris-hello-backend-aarch64-apple-darwin", "lunaris-hello-backend");
        std::env::set_var("LUNARIS_PORT", PORT.to_string());

        let app = tauri::test::mock_builder()
            .plugin(tauri_plugin_shell::init())
            .manage(BackendProcess::default())
            .build(tauri::test::mock_context(tauri::test::noop_assets()))
            .expect("build mock app");
        let handle = app.handle().clone();

        let start = start_backend(handle, app.state());
        assert!(start.ok, "start_backend failed: {}", start.message);

        let st = get_backend_status(app.state());
        assert!(st.running && st.pid.is_some(), "expected running");

        let body = poll_health(PORT, 25).expect("/api/health did not respond before timeout");
        assert!(body.contains("\"status\":\"ok\""), "unexpected health body: {body}");

        let stop = stop_backend(app.state());
        assert!(stop.ok, "stop_backend failed: {}", stop.message);
        assert!(wait_port_freed(PORT), "hello port not released after stop");
        assert!(!get_backend_status(app.state()).running, "expected stopped");
    }

    #[test]
    fn real_sidecar_spawn_health_kill() {
        const PORT: u16 = 18799;
        stage_sidecar("lunaris-real-backend-aarch64-apple-darwin", "lunaris-real-backend");
        std::env::set_var("LUNARIS_REAL_PORT", PORT.to_string());
        std::env::set_var(
            "LUNARIS_DATA_DIR",
            std::env::temp_dir().join("lunaris-real-test").to_string_lossy().to_string(),
        );

        let app = tauri::test::mock_builder()
            .plugin(tauri_plugin_shell::init())
            .manage(RealBackendProcess::default())
            .build(tauri::test::mock_context(tauri::test::noop_assets()))
            .expect("build mock app");
        let handle = app.handle().clone();

        let start = start_real_backend(handle, app.state());
        assert!(start.ok, "start_real_backend failed: {}", start.message);

        let st = get_real_backend_status(app.state());
        assert!(st.running && st.pid.is_some(), "expected real backend running");

        // Real backend cold start (unpack + sqlalchemy/pydantic import) is heavier.
        let body = poll_health(PORT, 30).expect("/api/health did not respond before timeout");
        assert!(body.contains("\"status\":\"ok\""), "unexpected health body: {body}");

        let stop = stop_real_backend(app.state());
        assert!(stop.ok, "stop_real_backend failed: {}", stop.message);
        assert!(wait_port_freed(PORT), "real port not released after stop");
        assert!(!get_real_backend_status(app.state()).running, "expected stopped");
    }
}
