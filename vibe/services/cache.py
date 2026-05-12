import hashlib
import json
from pathlib import Path


CACHE_DIR = Path(".vibe") / "cache"


def make_hash(*parts):
    hasher = hashlib.sha256()

    for part in parts:
        if part is None:
            part = ""

        hasher.update(str(part).encode("utf-8", errors="ignore"))

    return hasher.hexdigest()


def get_cache(key: str):
    path = CACHE_DIR / f"{key}.json"

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def set_cache(key: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    path = CACHE_DIR / f"{key}.json"
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )