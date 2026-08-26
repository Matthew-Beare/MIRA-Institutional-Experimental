# MIRA Desktop and CLI

MIRA uses one client contract across web, Windows, Linux and Android. The desktop application is a thin Tauri shell around the shared MIRA web UI; the CLI talks to the same versioned M.I.R.R.O.R. API.

## Desktop GUI

The Windows and Linux desktop binaries embed `../pwa` at build time. They provide the same capture, asset-photo, queue, dependency-status and API configuration surfaces as the web client while leaving canonical state on the server side.

The desktop shell never receives database credentials. Remote access uses the authenticated HTTPS API; a same-host Linux deployment may additionally expose a loopback/private local endpoint under the same authorization contract.

Camera support in the desktop shell depends on the platform WebView exposing the selected camera. UVC webcams and built-in cameras are therefore capability-tested at runtime. USB/Bluetooth HID barcode scanners do not depend on camera support and type directly into the capture field.

## CLI

`mira-cli` is built from the same Rust package as the desktop GUI and is intended for headless Linux, SSH, scripts and power users on Windows.

Examples:

- `mira-cli --api https://host/api health`
- `mira-cli --api https://host/api scan 036000291452 UPC_A`
- `mira-cli --api https://host/api asset <asset-uuid>`
- `mira-cli --api https://host/api upload-photo <asset-uuid> ./photo.jpg primary`
- `mira-cli --api https://host/api download-evidence <evidence-uuid> ./photo.jpg`

Set `MIRA_ACCESS_TOKEN` in the process environment. The CLI never writes that token to its own config files.

Asset pictures are intentionally not rendered in the CLI. Asset queries return photo/evidence UUIDs, hashes, MIME types, captions and URLs/locators permitted by the API. `download-evidence` retrieves the binary when the operator actually wants it.

## Build outputs

CI builds and uploads:

- `mira-desktop` for Linux;
- `mira-cli` for Linux;
- `mira-desktop.exe` for Windows;
- `mira-cli.exe` for Windows.

Packaging into MSI/NSIS, DEB/AppImage or distribution repositories is a release concern layered on top of these tested binaries; it does not change the application architecture.
