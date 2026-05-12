import json
import re
from pathlib import Path


CONTEXT_DIR = Path(".vibe")
CONTEXT_FILE = CONTEXT_DIR / "context.json"


def load_context():
    if not CONTEXT_FILE.exists():
        return {}

    try:
        return json.loads(CONTEXT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_context(data: dict):
    CONTEXT_DIR.mkdir(exist_ok=True)
    CONTEXT_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def update_context(updates: dict):
    context = load_context()
    context.update(updates)
    save_context(context)


def is_probably_file(path: str):
    path = path.strip().strip("`").strip()

    if not path:
        return False

    invalid_starts = (
        "python ",
        "pip ",
        "npm ",
        "node ",
        "curl ",
        "uvicorn ",
        "flask ",
        "source ",
        "export ",
    )

    lowered = path.lower()

    if lowered.startswith(invalid_starts):
        return False

    if "://" in path:
        return False

    valid_extensions = (
        ".py",
        ".js",
        ".html",
        ".css",
        ".json",
        ".md",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
    )

    return lowered.endswith(valid_extensions)


def extract_file_paths(text: str):
    patterns = [
        r"`([^`]+\.(py|js|html|css|json|toml|txt|md|yaml|yml))`",
        r"([\w./\\-]+\.(py|js|html|css|json|toml|txt|md|yaml|yml))",
    ]

    seen = set()
    files = []

    for pattern in patterns:
        for match in re.findall(pattern, text):
            file_path = match[0] if isinstance(match, tuple) else match
            cleaned = file_path.replace("\\", "/").strip()

            if not is_probably_file(cleaned):
                continue

            if cleaned in seen:
                continue

            seen.add(cleaned)
            files.append(cleaned)

    return files


def extract_relevance_scores(text: str):
    scores = {}

    pattern = r"-\s+(.+?):\s+([0-9.]+)"

    for file_path, score_text in re.findall(pattern, text):
        try:
            cleaned = file_path.strip().strip("`")
            scores[cleaned] = float(score_text)
        except ValueError:
            continue

    return scores


def find_checks_by_keywords(target: str):
    context = load_context()
    checks = context.get("checks", [])

    if not checks:
        return []

    target_words = {
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9_]+", target)
        if len(word) >= 3
    }

    if not target_words:
        return checks

    matched = []

    for check in checks:
        blob = " ".join([
            str(check.get("complaint", "")),
            str(check.get("file_path", "")),
            str(check.get("analysis", "")),
        ]).lower()

        if any(word in blob for word in target_words):
            matched.append(check)

    return matched