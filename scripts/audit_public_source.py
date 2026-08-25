#!/usr/bin/env python3
"""Audit public LyfeOS source for credentials, secrets, and mutable-data exports.

The public repository must not contain deployment identifiers or mutable personal
configuration merely because they are not authentication secrets. This audit
blocks credential material, concrete personal authority references, and files
that should never be source code.
Use --history in CI/release review to inspect added lines across reachable Git history.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

AUDITOR_PATH = "scripts/audit_public_source.py"
SYNTHETIC_SECRET_TEST_PATH = "tests/test_public_source_audit.py"
SCAN_EXEMPT_PATHS = {AUDITOR_PATH, SYNTHETIC_SECRET_TEST_PATH}
MAX_TEXT_BYTES = 2_000_000

BLOCKED_FILENAMES = {
    ".env",
    "credentials.json",
    "secrets.json",
    "service-account.json",
    "service_account.json",
}
BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".keystore",
    ".eml",
    ".mbox",
    ".pst",
    ".ost",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".dump",
    ".zip",
    ".7z",
    ".tar",
    ".gz",
    ".pyc",
}
TEXT_SUFFIXES = {
    "", ".css", ".csv", ".gitignore", ".html", ".ini", ".js", ".json",
    ".md", ".py", ".sh", ".svg", ".toml", ".tmpl", ".ts", ".txt",
    ".xml", ".yaml", ".yml",
}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("OpenAI/API-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("Stripe live secret", re.compile(r"\bsk_live_[0-9A-Za-z]{16,}\b")),
    ("basic-auth URL", re.compile(r"https?://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE)),
)

GENERIC_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|client_secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\b"
    r"\s*[:=]\s*[\"']([^\"']{8,})[\"']"
)
PLACEHOLDER_WORDS = {
    "placeholder",
    "example",
    "changeme",
    "redacted",
    "required",
    "optional",
    "your_",
    "user_selected",
}
CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
EMAIL_CANDIDATE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b")
GENERIC_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}
GOOGLE_RESOURCE_URL = re.compile(r"https://(?:docs|drive)\.google\.com/[^\s`\"')]+", re.IGNORECASE)
CONCRETE_AUTHORITY_ID = re.compile(
    r"(?i)\b(?:sheet|spreadsheet|drive|ops|mileage|purchase(?:/receipt)?|tool inventory)"
    r"[^\n]{0,48}\b(?:id|authority)\b\s*[:=`-]*\s*[`\"']?([A-Za-z0-9_-]{20,})"
)
DEPLOYMENT_ONLY_HEADING = re.compile(r"(?im)^#\s+Current Deployment Overrides\s*$")


def _git_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            [
                "git", "-C", str(root), "ls-files", "--cached", "--others",
                "--exclude-standard", "-z",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _blocked_path(relative: str) -> str | None:
    path = Path(relative)
    lower_name = path.name.lower()
    if lower_name in BLOCKED_FILENAMES:
        return f"forbidden credential/local-data filename: {relative}"
    if path.suffix.lower() in BLOCKED_SUFFIXES:
        return f"forbidden credential/mutable-data file type: {relative}"
    if lower_name.startswith(".env.") and lower_name != ".env.example":
        return f"forbidden environment file: {relative}"
    return None


def _luhn(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def scan_text(text: str, label: str) -> list[str]:
    errors: list[str] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{label}: possible {name}")

    for match in GENERIC_SECRET_ASSIGNMENT.finditer(text):
        value = match.group(2).strip().lower()
        if not any(word in value for word in PLACEHOLDER_WORDS):
            errors.append(f"{label}: possible literal secret assignment for {match.group(1)}")

    for match in CARD_CANDIDATE.finditer(text):
        if _luhn(match.group(0)):
            errors.append(f"{label}: possible full payment-card number")
            break
    for match in EMAIL_CANDIDATE.finditer(text):
        token = match.group(0)
        if (
            match.group(1).lower() not in GENERIC_EMAIL_DOMAINS
            and "{{" not in token
            and "YOUR_" not in token
        ):
            errors.append(f"{label}: concrete personal email address")
            break
    if GOOGLE_RESOURCE_URL.search(text):
        errors.append(f"{label}: concrete Google resource URL")
    if CONCRETE_AUTHORITY_ID.search(text):
        errors.append(f"{label}: concrete deployment authority ID")
    if DEPLOYMENT_ONLY_HEADING.search(text):
        errors.append(f"{label}: deployment-only override file in public source")
    return errors


def audit(root: Path) -> list[str]:
    if root.is_symlink():
        return [f"audit root must not be a symlink: {root}"]
    root = root.resolve()
    if not root.is_dir():
        return [f"audit root is not a directory: {root}"]
    errors: list[str] = []
    for path in _git_files(root):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if path.is_symlink():
            errors.append(f"forbidden symlink in public source: {relative}")
            continue
        blocked = _blocked_path(relative)
        if blocked:
            errors.append(blocked)
            continue
        if not path.exists():
            # A tracked path deleted in the candidate worktree has no current
            # content. Reachable historical content is handled by --history.
            continue
        if relative in SCAN_EXEMPT_PATHS:
            continue
        try:
            raw = path.read_bytes()
        except OSError as exc:
            errors.append(f"{relative}: unreadable: {exc}")
            continue
        text_like = path.suffix.lower() in TEXT_SUFFIXES or path.name == "LICENSE"
        if len(raw) > MAX_TEXT_BYTES:
            if text_like:
                errors.append(f"{relative}: text source exceeds audit size limit")
            continue
        if b"\0" in raw:
            if text_like:
                errors.append(f"{relative}: text source contains binary NUL bytes")
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            if text_like:
                errors.append(f"{relative}: text source is not valid UTF-8")
            continue
        errors.extend(scan_text(text, relative))
    return sorted(set(errors))


def audit_history(root: Path) -> list[str]:
    """Scan added text lines in reachable history, excluding synthetic detector tests."""
    try:
        result = subprocess.run(
            [
                "git", "-C", str(root), "log", "--all", "--format=commit:%H",
                "--no-ext-diff", "--unified=0", "--no-renames", "-p",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"history audit unavailable: {exc}"]

    errors: list[str] = []
    current_commit = "unknown"
    current_path = ""
    for raw_line in result.stdout.decode("utf-8", errors="replace").splitlines():
        if raw_line.startswith("commit:"):
            current_commit = raw_line.split(":", 1)[1]
            continue
        if raw_line.startswith("diff --git a/") and " b/" in raw_line:
            current_path = raw_line.split(" b/", 1)[1].strip('"')
            blocked = _blocked_path(current_path)
            if blocked:
                errors.append(f"history {current_commit[:12]}: {blocked}")
            continue
        if raw_line.startswith("+++ b/"):
            current_path = raw_line[6:]
            blocked = _blocked_path(current_path)
            if blocked:
                errors.append(f"history {current_commit[:12]}: {blocked}")
            continue
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        if current_path in SCAN_EXEMPT_PATHS:
            continue
        blocked = _blocked_path(current_path) if current_path else None
        if blocked:
            errors.append(f"history {current_commit[:12]}: {blocked}")
            continue
        line = raw_line[1:]
        errors.extend(scan_text(line, f"history {current_commit[:12]} {current_path or '<unknown>'}"))
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--history", action="store_true", help="also scan added lines across reachable Git history")
    args = parser.parse_args()

    errors = audit(args.root)
    if args.history:
        errors.extend(audit_history(args.root.resolve()))
        errors = sorted(set(errors))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Public source audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
