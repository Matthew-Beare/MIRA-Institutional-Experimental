"use strict";

const QUEUE_KEY = "mirror.capture.pending.v1";
const API_BASE_STORAGE_KEY = "mirror.capture.api-base.v1";
const CLIENT_KEY = "mirror.capture.client-id.v1";
const MAX_PHOTO_BYTES = 15 * 1024 * 1024;

const byId = (id) => document.getElementById(id);
const statusEl = byId("status");
const queueCountEl = byId("queueCount");
const videoEl = byId("camera");
let stream = null;
let detector = null;
let scanLoopActive = false;
let lastCameraValue = "";
let lastCameraAt = 0;
let previewUrl = null;

function setStatus(message) { statusEl.textContent = String(message || ""); }
function uuid() { if (globalThis.crypto?.randomUUID) return crypto.randomUUID(); throw new Error("This client requires crypto.randomUUID in a secure context."); }
function clientId() { let value = localStorage.getItem(CLIENT_KEY); if (!value) { value = uuid(); localStorage.setItem(CLIENT_KEY, value); } return value; }
function pending() { try { const rows = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]"); return Array.isArray(rows) ? rows : []; } catch { return []; } }
function savePending(rows) { localStorage.setItem(QUEUE_KEY, JSON.stringify(rows)); queueCountEl.textContent = `${rows.length} capture${rows.length === 1 ? "" : "s"} pending sync`; }
function apiBase() { return byId("apiBase").value.trim().replace(/\/+$/, ""); }
function token() { return byId("token").value.trim(); }

async function authorizedFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  return fetch(url, { ...options, headers });
}

function commandFor(rawValue, symbology) {
  const commandId = uuid();
  const capturedAt = new Date().toISOString();
  return {
    command_id: commandId,
    command_type: "capture.barcode_qr_scan",
    actor_id: `client:${clientId()}`,
    submitted_at: capturedAt,
    idempotency_key: `scan:${commandId}`,
    payload: { scan_uuid: commandId, captured_at: capturedAt, raw_value: rawValue, symbology: symbology || "UNKNOWN", client_id: clientId(), scan_class_candidate: "client_unverified" }
  };
}

async function submitCommand(command) {
  const base = apiBase();
  if (!base) throw new Error("No API base URL configured.");
  const response = await authorizedFetch(`${base}/v1/commands`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(command) });
  if (!response.ok) throw new Error(`API returned HTTP ${response.status}.`);
  const result = await response.json().catch(() => ({}));
  if (result?.readback_verified === false) throw new Error("Server did not verify canonical readback.");
  return result;
}

async function capture(rawValue, symbology) {
  const raw = String(rawValue || "").trim();
  if (!raw) return;
  const command = commandFor(raw, symbology);
  try { const result = await submitCommand(command); setStatus(`Submitted ${raw}\n${JSON.stringify(result, null, 2)}`); }
  catch (error) { const rows = pending(); if (!rows.some((row) => row.idempotency_key === command.idempotency_key)) rows.push(command); savePending(rows); setStatus(`Queued locally: ${raw}\n${error.message}`); }
  byId("scanValue").value = "";
  byId("scanValue").focus();
}

async function syncPending() {
  const rows = pending();
  if (!rows.length) { setStatus("Nothing pending."); return; }
  const remaining = []; let synced = 0;
  for (const command of rows) { try { await submitCommand(command); synced += 1; } catch { remaining.push(command); } }
  savePending(remaining); setStatus(`Synced ${synced}; ${remaining.length} remain pending.`);
}

function exportPending() {
  const blob = new Blob([JSON.stringify(pending(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `mirror-pending-captures-${new Date().toISOString().replace(/[:.]/g, "-")}.json`; anchor.click(); URL.revokeObjectURL(url);
}

async function makeDetector() {
  if (!("BarcodeDetector" in globalThis)) throw new Error("Camera barcode decoding is unavailable here. Use manual entry or a USB/Bluetooth keyboard-wedge scanner.");
  let formats = ["qr_code", "ean_13", "ean_8", "upc_a", "code_128"];
  if (typeof BarcodeDetector.getSupportedFormats === "function") { const supported = await BarcodeDetector.getSupportedFormats(); formats = formats.filter((format) => supported.includes(format)); }
  if (!formats.length) throw new Error("This runtime exposes BarcodeDetector but none of the requested formats.");
  return new BarcodeDetector({ formats });
}

async function cameraLoop() {
  if (!scanLoopActive || !detector || videoEl.readyState < 2) { if (scanLoopActive) requestAnimationFrame(cameraLoop); return; }
  try {
    const codes = await detector.detect(videoEl);
    if (codes.length) {
      const code = codes[0]; const value = String(code.rawValue || "").trim(); const now = Date.now();
      if (value && (value !== lastCameraValue || now - lastCameraAt > 2500)) { lastCameraValue = value; lastCameraAt = now; await capture(value, String(code.format || "UNKNOWN").toUpperCase()); }
    }
  } catch (error) { setStatus(`Camera decode error: ${error.message}`); }
  if (scanLoopActive) requestAnimationFrame(cameraLoop);
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error("Camera access requires a current secure browser/runtime.");
  detector = await makeDetector();
  stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
  videoEl.srcObject = stream; videoEl.hidden = false; await videoEl.play(); scanLoopActive = true; byId("startCamera").disabled = true; byId("stopCamera").disabled = false; setStatus("Camera scanner active."); requestAnimationFrame(cameraLoop);
}

function stopCamera() { scanLoopActive = false; if (stream) stream.getTracks().forEach((track) => track.stop()); stream = null; detector = null; videoEl.srcObject = null; videoEl.hidden = true; byId("startCamera").disabled = false; byId("stopCamera").disabled = true; setStatus("Camera stopped."); }

function previewPhoto() {
  const file = byId("photoFile").files?.[0]; const image = byId("photoPreview");
  if (previewUrl) URL.revokeObjectURL(previewUrl); previewUrl = null;
  if (!file) { image.hidden = true; image.removeAttribute("src"); return; }
  previewUrl = URL.createObjectURL(file); image.src = previewUrl; image.hidden = false;
}

async function uploadPhoto() {
  const base = apiBase(); const assetUuid = byId("photoAssetUuid").value.trim(); const role = byId("photoRole").value; const file = byId("photoFile").files?.[0];
  if (!base) throw new Error("No API base URL configured.");
  if (!assetUuid) throw new Error("Asset UUID is required.");
  if (!file) throw new Error("Choose an image first.");
  if (!file.type.startsWith("image/")) throw new Error("Asset media must be an image for this capture path.");
  if (file.size > MAX_PHOTO_BYTES) throw new Error("Image exceeds the 15 MiB client upload limit.");
  const form = new FormData(); form.set("asset_uuid", assetUuid); form.set("media_role", role); form.set("file", file, file.name);
  const response = await authorizedFetch(`${base}/v1/evidence`, { method: "POST", body: form });
  if (!response.ok) throw new Error(`Evidence API returned HTTP ${response.status}.`);
  const result = await response.json();
  if (result?.readback_verified === false) throw new Error("Evidence upload did not pass canonical readback.");
  setStatus(`Asset photo stored and linked.\n${JSON.stringify(result, null, 2)}`);
  byId("assetLookupUuid").value = assetUuid; await loadAsset();
}

function absoluteMediaUrl(value) {
  if (!value) return "";
  try { return new URL(value, `${apiBase()}/`).toString(); } catch { return ""; }
}

async function loadAsset() {
  const base = apiBase(); const assetUuid = byId("assetLookupUuid").value.trim();
  if (!base) throw new Error("No API base URL configured."); if (!assetUuid) throw new Error("Asset UUID is required.");
  const response = await authorizedFetch(`${base}/v1/assets/${encodeURIComponent(assetUuid)}`);
  if (!response.ok) throw new Error(`Asset API returned HTTP ${response.status}.`);
  const result = await response.json(); byId("assetResult").textContent = JSON.stringify(result, null, 2);
  const gallery = byId("assetPhotos"); gallery.replaceChildren();
  for (const photo of Array.isArray(result.photo_evidence) ? result.photo_evidence : []) {
    const src = absoluteMediaUrl(photo.thumbnail_url || photo.content_url);
    if (!src) continue;
    const image = document.createElement("img"); image.src = src; image.alt = photo.caption || photo.media_role || "Asset photo"; image.loading = "lazy"; gallery.appendChild(image);
  }
  setStatus("Asset read model loaded.");
}

function speakPreview() {
  const text = byId("speechText").value.trim(); if (!text) return;
  if (!("speechSynthesis" in globalThis)) { setStatus("Foreground speech preview is unavailable in this runtime."); return; }
  speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(text)); setStatus("Foreground TTS preview requested. This is not background reminder-delivery evidence.");
}

function initialize() {
  byId("apiBase").value = localStorage.getItem(API_BASE_STORAGE_KEY) || ""; savePending(pending());
  byId("saveSettings").addEventListener("click", () => { localStorage.setItem(API_BASE_STORAGE_KEY, apiBase()); setStatus("API address saved. Access token remains only in this page/session input."); });
  byId("scanForm").addEventListener("submit", async (event) => { event.preventDefault(); await capture(byId("scanValue").value, byId("symbology").value); });
  byId("startCamera").addEventListener("click", () => startCamera().catch((error) => setStatus(error.message)));
  byId("stopCamera").addEventListener("click", stopCamera);
  byId("syncPending").addEventListener("click", () => syncPending().catch((error) => setStatus(error.message)));
  byId("exportPending").addEventListener("click", exportPending);
  byId("speakTest").addEventListener("click", speakPreview);
  byId("photoFile").addEventListener("change", previewPhoto);
  byId("uploadPhoto").addEventListener("click", () => uploadPhoto().catch((error) => setStatus(error.message)));
  byId("loadAsset").addEventListener("click", () => loadAsset().catch((error) => setStatus(error.message)));
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch((error) => setStatus(`Service worker unavailable: ${error.message}`));
}

document.addEventListener("DOMContentLoaded", initialize);
