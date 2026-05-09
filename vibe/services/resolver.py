from pathlib import Path

IGNORE_DIRS = {
    "venv",
    ".git",
    "__pycache__",
    "node_modules",
    ".vibe",
}


def resolve_file(query: str):
    direct = Path(query)

    # Exact path provided
    if direct.exists() and direct.is_file():
        return direct, []

    matches = []

    for path in Path(".").rglob("*"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        if path.is_file() and path.name == query:
            matches.append(path)

    if len(matches) == 1:
        return matches[0], []

    return None, matches