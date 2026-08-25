#!/usr/bin/env python3
"""Fail when the portable starter contains production-specific/private markers."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_SUFFIXES = {".md", ".json", ".py", ".yml", ".yaml", ".txt", ".tmpl", ".toml"}
GENERIC_ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_symlink() and path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def audit(starter: Path, blocklist_path: Path) -> list[str]:
    if not starter.is_dir():
        return [f"starter root is not a directory: {starter}"]
    if not blocklist_path.is_file():
        return [f"blocklist is not a file: {blocklist_path}"]
    errors: list[str] = []
    blocked = [line.strip() for line in blocklist_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    email_re = re.compile(r"(?i)\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b")
    google_resource_re = re.compile(r"https://(?:docs|drive)\.google\.com/[^\s`\"')]+")
    authority_id_re = re.compile(
        r"(?i)\b(?:sheet|spreadsheet|drive|authority)\b[^\n]{0,48}\b(?:id|registry)\b"
        r"\s*[:=`-]*\s*[`\"']?([A-Za-z0-9_-]{20,})"
    )

    for path in sorted(starter.rglob("*")):
        if path.is_symlink():
            errors.append(f"{path.relative_to(starter)}: symlinks are forbidden in portable starter source")

    for path in iter_text_files(starter):
        rel = path.relative_to(starter)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: unreadable UTF-8 source: {exc}")
            continue
        for marker in blocked:
            if marker in text:
                errors.append(f"{rel}: contains blocked production marker")
        for match in email_re.finditer(text):
            domain = match.group(1).lower()
            token = match.group(0)
            if domain not in GENERIC_ALLOWED_EMAIL_DOMAINS and "{{" not in token and "YOUR_" not in token:
                errors.append(f"{rel}: contains non-placeholder email address")
        for match in google_resource_re.finditer(text):
            token = match.group(0)
            if "{{" not in token and "YOUR_" not in token and "example" not in token.lower():
                errors.append(f"{rel}: contains concrete Google resource URL")
        if authority_id_re.search(text):
            errors.append(f"{rel}: contains concrete deployment authority ID")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("starter", type=Path, nargs="?", default=Path("starter"))
    parser.add_argument("--blocklist", type=Path, default=Path("privacy/starter-blocklist.txt"))
    args = parser.parse_args()
    errors = audit(args.starter.resolve(), args.blocklist.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Starter privacy audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
