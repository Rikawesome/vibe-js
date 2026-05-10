import re
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".html",
    ".css",
}


IGNORE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
}


def should_skip(path: Path):
    return any(part in IGNORE_DIRS for part in path.parts)


def read_lines(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []


def detect_python_symbol(line: str):
    stripped = line.strip()

    patterns = [
        ("function", r"^(async\s+def|def)\s+([a-zA-Z_][\w]*)"),
        ("class", r"^class\s+([a-zA-Z_][\w]*)"),
        ("route", r"@(?:router|app)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]\)"),
    ]

    for symbol_type, pattern in patterns:
        match = re.search(pattern, stripped)

        if match:
            if symbol_type == "route":
                return {
                    "type": "route",
                    "name": match.group(2),
                    "meta": match.group(1).upper(),
                }

            return {
                "type": symbol_type,
                "name": match.group(2) if symbol_type == "function" else match.group(1),
                "meta": "",
            }

    return None


def detect_js_symbol(line: str):
    stripped = line.strip()

    patterns = [
        ("function", r"^function\s+([a-zA-Z_$][\w$]*)"),
        ("function", r"^(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s*)?\("),
        ("fetch", r"fetch\(\s*[`'\"]([^`'\"]+)"),
        ("dom_selector", r"getElementById\(['\"]([^'\"]+)['\"]\)"),
        ("dom_selector", r"querySelector\(['\"]([^'\"]+)['\"]\)"),
        ("event", r"\.addEventListener\(['\"]([^'\"]+)['\"]"),
        ("event", r"\.onclick\s*="),
    ]

    for symbol_type, pattern in patterns:
        match = re.search(pattern, stripped)

        if match:
            if symbol_type == "event" and ".onclick" in stripped:
                return {
                    "type": "event",
                    "name": "onclick",
                    "meta": stripped[:120],
                }

            return {
                "type": symbol_type,
                "name": match.group(1),
                "meta": "",
            }

    return None


def detect_html_symbol(line: str):
    stripped = line.strip()

    id_match = re.search(r'id=["\']([^"\']+)["\']', stripped)

    if id_match:
        return {
            "type": "html_id",
            "name": id_match.group(1),
            "meta": "",
        }

    return None


def detect_symbol(path: Path, line: str):
    suffix = path.suffix.lower()

    if suffix == ".py":
        return detect_python_symbol(line)

    if suffix == ".js":
        return detect_js_symbol(line)

    if suffix == ".html":
        return detect_html_symbol(line)

    return None


def estimate_symbol_range(lines, start_index):
    end_index = min(len(lines), start_index + 40)

    for index in range(start_index + 1, min(len(lines), start_index + 120)):
        line = lines[index]

        if line and not line.startswith((" ", "\t")):
            if (
                line.strip().startswith("def ")
                or line.strip().startswith("async def ")
                or line.strip().startswith("class ")
                or line.strip().startswith("function ")
                or line.strip().startswith("const ")
                or line.strip().startswith("let ")
                or line.strip().startswith("var ")
            ):
                end_index = index
                break

    return start_index + 1, end_index


def build_project_index(root="."):
    root_path = Path(root)
    symbols = []

    for path in root_path.rglob("*"):
        if should_skip(path):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        lines = read_lines(path)

        for index, line in enumerate(lines):
            symbol = detect_symbol(path, line)

            if not symbol:
                continue

            start_line, end_line = estimate_symbol_range(lines, index)

            symbols.append({
                "file_path": str(path),
                "symbol": symbol["name"],
                "type": symbol["type"],
                "meta": symbol.get("meta", ""),
                "start_line": start_line,
                "end_line": end_line,
            })

    return symbols


def format_project_index(symbols, limit=80):
    lines = []

    for item in symbols[:limit]:
        meta = f" [{item['meta']}]" if item.get("meta") else ""

        lines.append(
            f"- {item['file_path']}:{item['start_line']}-{item['end_line']} "
            f"{item['type']} {item['symbol']}{meta}"
        )

    if len(symbols) > limit:
        lines.append(f"...and {len(symbols) - limit} more symbols")

    return "\n".join(lines)