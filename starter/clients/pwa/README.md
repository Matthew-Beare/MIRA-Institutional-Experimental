# MIRA Capture PWA

This directory is a dependency-light installable client for Android, Windows and Linux.

## Run it

Serve this directory from the same authenticated HTTPS origin as the M.I.R.R.O.R. service, or configure the API base URL in the UI. For local development, `localhost` is a secure-context exception. Camera access and service workers generally do not work from arbitrary insecure HTTP origins.

The client submits `capture.barcode_qr_scan` command envelopes to `<API_BASE>/v1/commands`. The service remains responsible for authentication/authorization, canonical GTIN/tag validation, identifier resolution, state mutation, readback and audit.

## Scan methods

1. **Camera:** `getUserMedia` supplies the rear camera and the browser `BarcodeDetector` API decodes supported QR/UPC/EAN/Code-128 formats locally.
2. **USB/Bluetooth barcode gun:** keyboard-wedge/HID scanners type into the scan box. Configure the scanner to append Enter when possible and the form submits normally.
3. **Manual:** type or paste a value and select the known symbology if useful.

If the API is unavailable, commands are retained in a device-local pending queue using their original idempotency key. The user can retry sync or export pending JSON. A queued capture is not reported as canonically stored until the API succeeds.

## Speech preview

The `speechSynthesis` button proves only that the current foreground browser can synthesize the selected text. It is useful for wording/voice checks. It is **not** reliable background appointment delivery and must not set the deployment's `spoken_notification` capability healthy.

Dependable due-time spoken reminders are an Android-native capability: the companion receives a due reminder intent, creates the notification, passes the permitted speech text to Android Text-to-Speech, and Android routes the resulting audio to its selected device output.

## Security

- API tokens are not committed or embedded in the PWA source.
- The UI intentionally does not persist the token as durable app configuration.
- Database/provider credentials never enter the client.
- Camera decoding is only candidate capture; the canonical core remains authoritative.
