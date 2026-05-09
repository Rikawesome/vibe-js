from pathlib import Path
import json

VIBE_DIR = Path(".vibe")
CONTEXT_FILE = VIBE_DIR / "context.json"


def save_context(data: dict):
    VIBE_DIR.mkdir(exist_ok=True)

    with open(CONTEXT_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_context():
    if not CONTEXT_FILE.exists():
        return None

    with open(CONTEXT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
def update_context(updates: dict):
    data = load_context() or {}
    data.update(updates)
    save_context(data)
def find_checks_by_keywords(query: str):
    data = load_context() or {}
    checks = data.get("checks", [])

    if not checks:
        last_check = data.get("last_check")
        if last_check:
            checks = [last_check]

    words = [
        word.lower()
        for word in query.split()
        if len(word) > 2
    ]

    matched = []

    for check in checks:
        searchable = " ".join([
            check.get("complaint", ""),
            check.get("file_path", ""),
            check.get("analysis", ""),
        ]).lower()

        score = sum(1 for word in words if word in searchable)

        if score > 0:
            matched.append((score, check))

    matched.sort(key=lambda item: item[0], reverse=True)

    return [check for score, check in matched]


def find_check_by_keywords(query: str):
    matches = find_checks_by_keywords(query)
    return matches[0] if matches else None