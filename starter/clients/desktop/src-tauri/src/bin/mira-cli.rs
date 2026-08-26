use chrono::Utc;
use reqwest::blocking::{multipart, Client};
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE};
use serde_json::{json, Value};
use std::env;
use std::error::Error;
use std::fs;
use std::path::Path;
use uuid::Uuid;

fn usage() -> ! {
    eprintln!("MIRA CLI\n\nUsage:\n  mira-cli [--api URL] health\n  mira-cli [--api URL] scan VALUE [SYMBOLOGY]\n  mira-cli [--api URL] asset ASSET_UUID\n  mira-cli [--api URL] upload-photo ASSET_UUID FILE [ROLE]\n  mira-cli [--api URL] download-evidence EVIDENCE_UUID OUTPUT\n\nEnvironment:\n  MIRA_API_BASE       API base URL when --api is omitted\n  MIRA_ACCESS_TOKEN   scoped bearer token; never persisted by this CLI");
    std::process::exit(2);
}

fn parse_args() -> (String, Vec<String>) {
    let mut args: Vec<String> = env::args().skip(1).collect();
    let mut api = env::var("MIRA_API_BASE").unwrap_or_default();
    if args.first().map(String::as_str) == Some("--api") {
        if args.len() < 3 { usage(); }
        api = args[1].clone();
        args.drain(0..2);
    }
    if api.trim().is_empty() { usage(); }
    (api.trim_end_matches('/').to_string(), args)
}

fn client() -> Result<Client, Box<dyn Error>> {
    Ok(Client::builder().user_agent("mira-cli/0.1").build()?)
}

fn auth(req: reqwest::blocking::RequestBuilder) -> reqwest::blocking::RequestBuilder {
    match env::var("MIRA_ACCESS_TOKEN") {
        Ok(token) if !token.trim().is_empty() => req.header(AUTHORIZATION, format!("Bearer {}", token.trim())),
        _ => req,
    }
}

fn print_json(value: &Value) -> Result<(), Box<dyn Error>> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

fn get_json(base: &str, path: &str) -> Result<(), Box<dyn Error>> {
    let response = auth(client()?.get(format!("{}{}", base, path))).send()?.error_for_status()?;
    print_json(&response.json()?)
}

fn post_json(base: &str, path: &str, body: &Value) -> Result<(), Box<dyn Error>> {
    let response = auth(client()?.post(format!("{}{}", base, path))).json(body).send()?.error_for_status()?;
    print_json(&response.json()?)
}

fn scan(base: &str, value: &str, symbology: &str) -> Result<(), Box<dyn Error>> {
    let command_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();
    let body = json!({
        "command_id": command_id,
        "command_type": "capture.barcode_qr_scan",
        "actor_id": "client:mira-cli",
        "submitted_at": now,
        "idempotency_key": format!("scan:{}", command_id),
        "payload": {
            "scan_uuid": command_id,
            "captured_at": now,
            "raw_value": value,
            "symbology": symbology,
            "client_id": "mira-cli",
            "scan_class_candidate": "client_unverified"
        }
    });
    post_json(base, "/v1/commands", &body)
}

fn mime_for(path: &Path) -> &'static str {
    match path.extension().and_then(|v| v.to_str()).unwrap_or("").to_ascii_lowercase().as_str() {
        "jpg" | "jpeg" => "image/jpeg",
        "png" => "image/png",
        "webp" => "image/webp",
        "heic" => "image/heic",
        _ => "application/octet-stream",
    }
}

fn upload_photo(base: &str, asset_uuid: &str, file_path: &str, role: &str) -> Result<(), Box<dyn Error>> {
    let path = Path::new(file_path);
    let bytes = fs::read(path)?;
    let file_name = path.file_name().and_then(|v| v.to_str()).unwrap_or("asset-photo").to_string();
    let part = multipart::Part::bytes(bytes).file_name(file_name).mime_str(mime_for(path))?;
    let form = multipart::Form::new()
        .text("asset_uuid", asset_uuid.to_string())
        .text("media_role", role.to_string())
        .part("file", part);
    let response = auth(client()?.post(format!("{}/v1/evidence", base))).multipart(form).send()?.error_for_status()?;
    print_json(&response.json()?)
}

fn download_evidence(base: &str, evidence_uuid: &str, output: &str) -> Result<(), Box<dyn Error>> {
    let response = auth(client()?.get(format!("{}/v1/evidence/{}", base, evidence_uuid))).send()?.error_for_status()?;
    let content_type = response.headers().get(CONTENT_TYPE).and_then(|v| v.to_str().ok()).unwrap_or("application/octet-stream").to_string();
    let bytes = response.bytes()?;
    fs::write(output, &bytes)?;
    println!("saved {} bytes to {} ({})", bytes.len(), output, content_type);
    Ok(())
}

fn run() -> Result<(), Box<dyn Error>> {
    let (base, args) = parse_args();
    if args.is_empty() { usage(); }
    match args[0].as_str() {
        "health" if args.len() == 1 => get_json(&base, "/v1/health"),
        "scan" if args.len() == 2 || args.len() == 3 => scan(&base, &args[1], args.get(2).map(String::as_str).unwrap_or("UNKNOWN")),
        "asset" if args.len() == 2 => get_json(&base, &format!("/v1/assets/{}", args[1])),
        "upload-photo" if args.len() == 3 || args.len() == 4 => upload_photo(&base, &args[1], &args[2], args.get(3).map(String::as_str).unwrap_or("gallery")),
        "download-evidence" if args.len() == 3 => download_evidence(&base, &args[1], &args[2]),
        _ => usage(),
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("error: {error}");
        std::process::exit(1);
    }
}
