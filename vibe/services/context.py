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