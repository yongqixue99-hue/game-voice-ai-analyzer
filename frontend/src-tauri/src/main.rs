use serde::Serialize;
use std::env;
use std::sync::Mutex;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

const DEFAULT_BACKEND_PORT: u16 = 8000;
const SIDECAR_NAME: &str = "lunaris-hello-backend";
const DEFAULT_SIDECAR_PORT: u16 = 8765;

/// Holds the handle to the sidecar backend process, if Tauri started one.
#[derive(Default)]
struct BackendProcess(Mutex<Option<CommandChild>>);

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

/// Port the sidecar binds to. Honors LUNARIS_PORT, else falls back to 8765.
fn sidecar_port() -> u16 {
    env::var("LUNARIS_PORT")
        .ok()
        .and_then(|p| p.trim().parse::<u16>().ok())
        .unwrap_or(DEFAULT_SIDECAR_PORT)
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
        return BackendActionResult {
            ok: true,
            mode: "sidecar",
            message: "后端已在运行。".into(),
        };
    }

    let port = sidecar_port();
    let command = match app.shell().sidecar(SIDECAR_NAME) {
        Ok(cmd) => cmd
            .env("LUNARIS_PORT", port.to_string())
            .env("LUNARIS_HOST", "127.0.0.1"),
        Err(e) => {
            return BackendActionResult {
                ok: false,
                mode: "sidecar",
                message: format!("无法定位 sidecar：{e}"),
            }
        }
    };

    match command.spawn() {
        Ok((mut rx, child)) => {
            // Drain the event channel so the child never blocks on stdout/stderr.
            tauri::async_runtime::spawn(async move { while rx.recv().await.is_some() {} });
            *guard = Some(child);
            BackendActionResult {
                ok: true,
                mode: "sidecar",
                message: format!("已启动 hello-backend，端口 {port}。"),
            }
        }
        Err(e) => BackendActionResult {
            ok: false,
            mode: "sidecar",
            message: format!("启动失败：{e}"),
        },
    }
}

#[tauri::command]
fn stop_backend(state: tauri::State<BackendProcess>) -> BackendActionResult {
    let mut guard = state.0.lock().unwrap();
    let Some(child) = guard.take() else {
        return BackendActionResult {
            ok: true,
            mode: "stopped",
            message: "后端未在运行。".into(),
        };
    };
    match terminate_backend(child.pid(), child) {
        Ok(()) => BackendActionResult {
            ok: true,
            mode: "stopped",
            message: "已停止后端。".into(),
        },
        Err(e) => BackendActionResult {
            ok: false,
            mode: "sidecar",
            message: format!("停止失败：{e}"),
        },
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
        .invoke_handler(tauri::generate_handler![
            get_api_base_url,
            get_runtime_info,
            get_backend_status,
            start_backend,
            stop_backend,
        ])
        .run(tauri::generate_context!())
        .expect("error while running LUNARIS Tauri shell");
}

#[cfg(test)]
mod sidecar_tests {
    use super::*;
    use tauri::Manager;
    use std::path::PathBuf;
    use std::process::Command as StdCommand;
    use std::time::Duration;

    const TEST_PORT: u16 = 8799;

    /// plugin-shell resolves the sidecar relative to the current exe; under
    /// `cargo test` that's target/debug/deps/, so place the verified binary there.
    fn stage_sidecar() {
        let src = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("binaries/lunaris-hello-backend-aarch64-apple-darwin");
        let exe_dir = std::env::current_exe().unwrap().parent().unwrap().to_path_buf();
        std::fs::copy(&src, exe_dir.join("lunaris-hello-backend")).expect("stage sidecar");
    }

    fn curl_health() -> Option<String> {
        let out = StdCommand::new("curl")
            .args(["-s", "-m", "3", &format!("http://127.0.0.1:{TEST_PORT}/api/health")])
            .output()
            .ok()?;
        let body = String::from_utf8_lossy(&out.stdout).to_string();
        (!body.trim().is_empty()).then_some(body)
    }

    #[test]
    fn sidecar_spawn_health_kill() {
        stage_sidecar();
        std::env::set_var("LUNARIS_PORT", TEST_PORT.to_string());

        let app = tauri::test::mock_builder()
            .plugin(tauri_plugin_shell::init())
            .manage(BackendProcess::default())
            .build(tauri::test::mock_context(tauri::test::noop_assets()))
            .expect("build mock app");
        let handle = app.handle().clone();

        let start = start_backend(handle, app.state());
        assert!(start.ok, "start_backend failed: {}", start.message);

        let st = get_backend_status(app.state());
        assert!(st.running && st.pid.is_some(), "expected running, got {st:?}", st = (st.running, st.pid));

        // PyInstaller onefile cold start (unpack + import) can take ~10s.
        let mut health = None;
        for _ in 0..25 {
            std::thread::sleep(Duration::from_millis(800));
            health = curl_health();
            if health.is_some() {
                break;
            }
        }
        let body = health.expect("/api/health did not respond before timeout");
        assert!(body.contains("\"status\":\"ok\""), "unexpected health body: {body}");

        let stop = stop_backend(app.state());
        assert!(stop.ok, "stop_backend failed: {}", stop.message);

        // The real server child (not just internal state) must release the port.
        let mut freed = false;
        for _ in 0..10 {
            std::thread::sleep(Duration::from_millis(500));
            if curl_health().is_none() {
                freed = true;
                break;
            }
        }
        assert!(freed, "/api/health still served after stop_backend: port not released");

        let st2 = get_backend_status(app.state());
        assert!(!st2.running, "expected stopped after stop_backend");
    }
}
