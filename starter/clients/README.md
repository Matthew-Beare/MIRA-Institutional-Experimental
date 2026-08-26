# M.I.R.R.O.R. client surfaces

M.I.R.R.O.R. uses one versioned service/API contract across **web, Windows, Linux and Android**. The user interface is shared wherever practical; operating-system helpers exist only for capabilities the browser cannot reliably provide.

## Web / PWA

`clients/pwa/` is the shared GUI. It provides camera barcode/QR capture where `BarcodeDetector` is available, manual capture, USB/Bluetooth keyboard-wedge scanning, offline idempotent scan queueing, asset-photo capture/preview/upload, asset lookup/photo gallery, and foreground speech preview.

It is installable as a PWA and can also be served as the normal web interface. Camera access requires a secure context and is runtime capability-tested rather than assumed.

## Windows and Linux desktop

`clients/desktop/` is a Tauri shell that embeds the same PWA assets and builds native Windows and Linux GUI binaries. The same Rust package also builds `mira-cli` for terminal/SSH/script use.

The GUI shows asset images when authorized. The CLI deliberately stays textual: it shows Evidence UUID, MIME/hash/caption/provenance metadata and can explicitly download a selected image.

Linux can additionally host the always-on M.I.R.R.O.R. service, provider adapters, `systemd` scheduling, local-model runtime and hardware bridges. Windows remains a fully supported interactive client and may host local adapters where useful.

## Android

The PWA remains the shared visual/capture surface. The native Android companion supplies the capabilities mobile browsers cannot reliably guarantee:

- background appointment notifications;
- Android Text-to-Speech at reminder due time;
- Android-selected audio routing, including compatible Bluetooth hearing aids/headsets;
- exact/fallback alarm scheduling with device verification;
- NFC/native hardware hooks.

**Android's selected Text-to-Speech engine generates the actual voice locally.** M.I.R.R.O.R. supplies the canonical reminder text/timing/privacy policy; it does not render an audio file or claim direct control of the Bluetooth route.

CI builds an installable debug APK for testing. A public production/release APK later requires a deployment signing key kept outside Git.

## Cameras, barcode scanners, RFID and printers

Hardware compatibility is capability/transport based; see `../hardware-capture-contract.json`.

- built-in/USB UVC cameras may work through browser/WebView `MediaDevices` when exposed by the runtime;
- Android native camera is a separate adapter path;
- 1D laser, CCD and 2D imagers work immediately when they present as USB/Bluetooth HID keyboard-wedge scanners;
- serial/USB-CDC scanners use a local-agent adapter on Windows/Linux;
- NFC/HF/UHF RFID feeds the shared identifier/presence event model and never silently moves an asset from one passive read;
- normal printers use browser/OS printing; Linux CUPS and Windows spooler are baseline transports;
- thermal label printers may use normal drivers or explicit ZPL/EPL/TSPL/raw-TCP/USB adapters.

Printer type, scanner brand or storage provider never becomes canonical identity.

## Asset media

Asset pictures are Evidence objects linked to immutable Asset UUIDs under `../asset-media-contract.json`. Drive, OneDrive/SharePoint, filesystem-backed evidence and S3-compatible object storage are interchangeable adapters. Moving from Drive to private object storage does not renumber the asset or its Evidence UUID.

## Security boundary

All clients talk to `../client-api-contract.json`. They do not connect directly to PostgreSQL, Google Sheets, Microsoft Lists, Drive or object storage. Database/provider credentials remain server-side. Client tokens are scoped, and long-lived credentials require an OS secret-store adapter rather than source files or browser-local plaintext.
