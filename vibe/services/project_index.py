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
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()
    except Exception:
        return []


def detect_python_symbol(line: str):
    stripped = line.strip()

    patterns = [
        ("function", r"^(async\s+def|def)\s+([a-zA-Z_][\w]*)"),
        ("class", r"^class\s+([a-zA-Z_][\w]*)"),
        (
            "route",
            r"@(?:router|app)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]\)",
        ),
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
                "name": (
                    match.group(2)
                    if symbol_type == "function"
                    else match.group(1)
                ),
                "meta": "",
            }

    return None


def detect_js_symbol(line: str):
    stripped = line.strip()

    patterns = [
        ("function", r"^function\s+([a-zA-Z_$][\w$]*)"),
        (
            "function",
            r"^(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s*)?\(",
        ),
        ("fetch", r"fetch\(\s*[`'\"]([^`'\"]+)"),
        ("network", r"fetch\(\s*[`'\"]([^`'\"]+)"),
        ("dom_selector", r"getElementById\(['\"]([^'\"]+)['\"]\)"),
        ("dom_selector", r"querySelector\(['\"]([^'\"]+)['\"]\)"),
        ("event", r"\.addEventListener\(['\"]([^'\"]+)['\"]"),
        ("event", r"\.onclick\s*="),

        # Generic media / browser lifecycle symbols
        ("media", r"new\s+Audio\s*\("),
        ("media", r"\.play\s*\("),
        ("media", r"\.pause\s*\("),
        ("media", r"\.blob\s*\("),
        ("media", r"createObjectURL\s*\("),
        ("media", r"\.src\s*="),
        ("media", r"AudioContext\s*\("),

        # Generic browser state symbols
        ("storage", r"localStorage\."),
        ("storage", r"sessionStorage\."),
    ]

    for symbol_type, pattern in patterns:
        match = re.search(pattern, stripped)

        if not match:
            continue

        if symbol_type == "event" and ".onclick" in stripped:
            return {
                "type": "event",
                "name": "onclick",
                "meta": stripped[:120],
            }

        if symbol_type in {"media", "storage"}:
            return {
                "type": symbol_type,
                "name": stripped[:100],
                "meta": "",
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

    class_match = re.search(r'class=["\']([^"\']+)["\']', stripped)

    if class_match:
        return {
            "type": "html_class",
            "name": class_match.group(1),
            "meta": "",
        }

    return None


def detect_css_symbol(line: str):
    stripped = line.strip()

    match = re.match(r"([.#][a-zA-Z_][\w-]*)\s*\{", stripped)

    if match:
        return {
            "type": "css_selector",
            "name": match.group(1),
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

    if suffix == ".css":
        return detect_css_symbol(line)

    return None


def estimate_symbol_range(lines, start_index):
    end_index = min(len(lines), start_index + 40)

    for index in range(
        start_index + 1,
        min(len(lines), start_index + 120),
    ):
        line = lines[index]

        if line and not line.startswith((" ", "\t")):
            stripped = line.strip()

            if (
                stripped.startswith("def ")
                or stripped.startswith("async def ")
                or stripped.startswith("class ")
                or stripped.startswith("function ")
                or stripped.startswith("const ")
                or stripped.startswith("let ")
                or stripped.startswith("var ")
                or stripped.startswith("@router.")
                or stripped.startswith("@app.")
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

            start_line, end_line = estimate_symbol_range(
                lines,
                index,
            )

            symbols.append({
                "file_path": str(path),
                "symbol": symbol["name"],
                "type": symbol["type"],
                "meta": symbol.get("meta", ""),
                "start_line": start_line,
                "end_line": end_line,
            })

    return symbols


def format_project_index(symbols, limit=120):
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