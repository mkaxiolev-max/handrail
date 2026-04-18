#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    // Hard gate: Alexandria must be mounted before NS∞ can operate
    if !std::path::Path::new("/Volumes/NSExternal").exists() {
        let _ = std::process::Command::new("osascript")
            .args([
                "-e",
                concat!(
                    "display dialog ",
                    "\"NS\\u221e cannot start.\\n\\n",
                    "Alexandria (/Volumes/NSExternal) is not mounted.\\n\\n",
                    "Please connect the NS External drive and relaunch.\" ",
                    "buttons {\"OK\"} default button \"OK\" ",
                    "with title \"NS\\u221e Boot Error\" with icon stop"
                ),
            ])
            .status();
        std::process::exit(1);
    }

    // Spawn lightweight boot helper (non-blocking — window loads in parallel)
    let home = std::env::var("HOME").unwrap_or_default();
    let boot = format!("{}/axiolev_runtime/apps/ns_tauri_boot.sh", home);
    if std::path::Path::new(&boot).exists() {
        let _ = std::process::Command::new("bash")
            .arg(&boot)
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn();
    }

    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running NS∞");
}
