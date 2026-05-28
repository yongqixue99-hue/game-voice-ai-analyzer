fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running LUNARIS Tauri shell");
}
