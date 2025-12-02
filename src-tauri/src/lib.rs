use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct TranscribeConfig {
    file_path: String,
    api_key: String,
    language: Option<String>,
    model: Option<String>,
    prompt: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct TranscribeResult {
    success: bool,
    text: Option<String>,
    error: Option<String>,
    duration: Option<f64>,
    chunks: Option<i32>,
}

#[tauri::command]
async fn transcribe_audio(config: TranscribeConfig) -> Result<TranscribeResult, String> {
    // Construir path al CLI de Python (por ahora solo modo desarrollo)
    let python_cli = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("python-engine")
        .join("cli.py");

    // Preparar JSON de configuración
    let config_json = serde_json::to_string(&config)
        .map_err(|e| format!("Error serializando config: {}", e))?;

    // Ejecutar Python subprocess
    let output = Command::new("python3")
        .arg(python_cli)
        .arg("transcribe")
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .and_then(|mut child| {
            use std::io::Write;
            if let Some(mut stdin) = child.stdin.take() {
                stdin.write_all(config_json.as_bytes())?;
            }
            child.wait_with_output()
        })
        .map_err(|e| format!("Error ejecutando Python: {}", e))?;

    // Parsear resultado
    if output.status.success() {
        let result_str = String::from_utf8_lossy(&output.stdout);
        serde_json::from_str::<TranscribeResult>(&result_str)
            .map_err(|e| format!("Error parseando resultado: {}", e))
    } else {
        let error_str = String::from_utf8_lossy(&output.stderr);
        Ok(TranscribeResult {
            success: false,
            text: None,
            error: Some(error_str.to_string()),
            duration: None,
            chunks: None,
        })
    }
}

#[tauri::command]
async fn test_api_key(api_key: String) -> Result<bool, String> {
    let python_cli = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("python-engine")
        .join("cli.py");

    let output = Command::new("python3")
        .arg(python_cli)
        .arg("test_api")
        .arg(&api_key)
        .output()
        .map_err(|e| format!("Error ejecutando Python: {}", e))?;

    Ok(output.status.success())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .invoke_handler(tauri::generate_handler![
            transcribe_audio,
            test_api_key
        ])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
