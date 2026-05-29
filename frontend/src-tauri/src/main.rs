use serde::Serialize;
use std::env;

const DEFAULT_BACKEND_PORT: u16 = 8000;

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
    note: &'static str,
    api_base_url: String,
}

#[derive(Serialize)]
struct BackendActionResult {
    ok: bool,
    mode: &'static str,
    message: &'static str,
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
        backend_management_mode: "external_dev",
        data_dir_override: env::var("LUNARIS_DATA_DIR").ok(),
    }
}

#[tauri::command]
fn get_backend_status() -> BackendStatus {
    BackendStatus {
        mode: "external_dev",
        note: "P1 control plane skeleton: backend lifecycle is managed externally (scripts/dev-all.sh or manual uvicorn). Tauri does not spawn or kill any backend process in this phase.",
        api_base_url: resolve_api_base_url().url,
    }
}

#[tauri::command]
fn start_backend() -> BackendActionResult {
    BackendActionResult {
        ok: false,
        mode: "external_dev",
        message: "P1 占位：当前由开发者通过 scripts/dev-all.sh 或 uvicorn 启动后端，Tauri 不会自动拉起 FastAPI。后续 change（tauri-prod-backend-pyinstaller）会接管该能力。",
    }
}

#[tauri::command]
fn stop_backend() -> BackendActionResult {
    BackendActionResult {
        ok: false,
        mode: "external_dev",
        message: "P1 占位：Tauri 不会主动停止后端进程，避免误杀用户手动启动的 uvicorn。",
    }
}

fn main() {
    tauri::Builder::default()
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
