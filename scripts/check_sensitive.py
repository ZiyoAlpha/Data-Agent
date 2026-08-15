"""Conservative public-release scan for common secrets and private artifacts."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "__pycache__", ".dataagent"}
SKIP_FILES = {".env"}
PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "password assignment": re.compile(r"(?i)\bpassword\s*[:=]\s*[^\s$<{][^\s]{5,}"),
}
FORBIDDEN_NAMES = {"password.txt", "credentials.json", "secrets.json", ".env.local"}


def files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def main() -> int:
    findings = []
    for path in files():
        relative = path.relative_to(ROOT)
        if path.name.lower() in FORBIDDEN_NAMES:
            findings.append(f"forbidden filename: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"unexpected binary file: {relative}")
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
    if findings:
        print("Sensitive-information scan failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Sensitive-information scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

