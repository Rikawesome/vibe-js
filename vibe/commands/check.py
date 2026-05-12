from rich.console import Console
from rich.panel import Panel
import typer
import re
from vibe.prompts.prompts import MULTI_CHECK_PROMPT
from vibe.services import files
from vibe.services.ai import ask_ai
from vibe.services.context import (
    load_context,
    update_context,
    extract_relevance_scores,
)
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file
from vibe.services.cache import make_hash, get_cache, set_cache

console = Console()

MAX_FILE_CHARS = 6000


def dedupe_files(files: list[str]):
    deduped_files = []
    seen_files = set()

    for file in files:
        normalized = file.replace("\\", "/").strip()

        if normalized in seen_files:
            continue

        seen_files.add(normalized)
        deduped_files.append(file)

    return deduped_files


def find_score_for_file(scores: dict, file_path: str):
    normalized_file = file_path.replace("\\", "/").strip().lower()

    for scored_path, score in scores.items():
        normalized_scored = scored_path.replace("\\", "/").strip().lower()

        if normalized_scored == normalized_file:
            return score

        if normalized_file.endswith(normalized_scored):
            return score

        if normalized_scored.endswith(normalized_file):
            return score

    return 0.3

def extract_complaint_words(complaint: str):
    stop_words = {
        "this", "that", "with", "from", "when", "what",
        "where", "after", "before", "into", "have",
        "does", "dont", "doesnt", "isnt", "cant",
        "could", "would", "should", "sometimes",
        "still", "just", "like", "the", "and", "but",
    }

    words = []

    for raw in complaint.replace("_", " ").replace("-", " ").split():
        word = "".join(char for char in raw.lower() if char.isalnum())

        if len(word) < 4:
            continue

        if word in stop_words:
            continue

        words.append(word)

    return set(words)


def find_relevant_symbols(code: str, complaint: str):
    complaint_words = extract_complaint_words(complaint)

    baseline_keywords = {
        "error",
        "fetch",
        "api",
        "route",
        "onclick",
        "addeventlistener",
        "submit",
        "click",
        "input",
        "form",
        "async",
        "await",
        "function",
        "class",
        "def",
        "import",
        "router",
        "response",
        "json",
        "blob",
        "render",
        "redirect",
        "token",
        "auth",
    }

    return complaint_words | baseline_keywords
def get_symbol_ranges_for_file(context: dict, file_path: str):
    symbols = context.get("project_symbols", [])
    complaint_words = extract_complaint_words(
        context.get("complaint", "")
    )

    normalized_file = file_path.replace("\\", "/").strip().lower()
    matched_ranges = []

    for symbol in symbols:
        symbol_file = symbol.get("file_path", "")
        normalized_symbol_file = (
            symbol_file.replace("\\", "/").strip().lower()
        )

        if not (
            normalized_file.endswith(normalized_symbol_file)
            or normalized_symbol_file.endswith(normalized_file)
        ):
            continue

        symbol_name = str(symbol.get("symbol", "")).lower()
        symbol_type = str(symbol.get("type", "")).lower()
        symbol_meta = str(symbol.get("meta", "")).lower()
        searchable = f"{symbol_name} {symbol_type} {symbol_meta} {normalized_symbol_file}"

        score = 0

        for word in complaint_words:
            if word in searchable:
                score += 3

        if symbol_type in {
            "route",
            "fetch",
            "event",
            "dom_selector",
            "function",
            "class",
        }:
            score += 1

        # Keep useful structural symbols, but prioritize complaint matches.
        if score <= 0:
            continue

        matched_ranges.append({
            "symbol": symbol.get("symbol", ""),
            "type": symbol.get("type", ""),
            "start_line": symbol.get("start_line", 1),
            "end_line": symbol.get("end_line", 1),
            "score": score,
        })

    matched_ranges.sort(
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    return matched_ranges[:12]

def build_smart_context(code: str, file_path: str, complaint: str, symbol_ranges=None):
    if len(code) <= MAX_FILE_CHARS:
        return code

    complaint_words = [
        word.lower()
        for word in complaint.replace("_", " ").replace("-", " ").split()
        if len(word) >= 4
    ]

    useful_keywords = find_relevant_symbols(code, complaint)

    fallback_keywords = [
        "error",
        "fetch",
        "api",
        "route",
        "onclick",
        "addeventlistener",
        "audio",
        "play",
        "tts",
        "localstorage",
        "async",
        "await",
        "function",
        "class",
        "def",
        "import",
        "router",
        "response",
        "blob",
        "createobjecturl",
    ]

    useful_keywords.update(fallback_keywords)

    lines = code.splitlines()
    selected_ranges = []
    if symbol_ranges:
        for symbol in symbol_ranges:
            start = max(0, int(symbol["start_line"]) - 8)
            end = min(len(lines), int(symbol["end_line"]) + 12)
            selected_ranges.append((start, end))

    for index, line in enumerate(lines):
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in useful_keywords):
            start = max(0, index - 20)
            end = min(len(lines), index + 35)
            selected_ranges.append((start, end))

    if not selected_ranges:
        head = "\n".join(lines[:120])
        tail = "\n".join(lines[-80:])

        return (
            head
            + "\n\n...FILE MIDDLE TRUNCATED FOR TOKEN LIMIT...\n\n"
            + tail
        )[:MAX_FILE_CHARS]

    merged_ranges = []

    for start, end in selected_ranges:
        if not merged_ranges:
            merged_ranges.append([start, end])
            continue

        previous = merged_ranges[-1]

        if start <= previous[1] + 5:
            previous[1] = max(previous[1], end)
        else:
            merged_ranges.append([start, end])

    chunks = []

    for start, end in merged_ranges:
        chunk = "\n".join(lines[start:end])

        chunks.append(
            f"...SNIPPET {start + 1}-{end} FROM {file_path}...\n{chunk}"
        )

    smart_context = "\n\n".join(chunks)

    if len(smart_context) > MAX_FILE_CHARS:
        smart_context = (
            smart_context[:MAX_FILE_CHARS]
            + "\n\n...SMART CONTEXT TRUNCATED FOR TOKEN LIMIT..."
        )

    return smart_context


def extract_routes(code: str):
    routes = []

    route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'

    lines = code.splitlines()

    for index, line in enumerate(lines):
        match = re.search(route_pattern, line.strip())

        if not match:
            continue

        method = match.group(1).upper()
        path = match.group(2)

        handler = "unknown_handler"

        for next_line in lines[index + 1:index + 6]:
            stripped = next_line.strip()

            if stripped.startswith("async def ") or stripped.startswith("def "):
                handler = stripped
                break

        routes.append({
            "method": method,
            "path": path,
            "handler": handler,
        })

    return routes


def extract_fetches(code: str):
    fetches = []

    fetch_pattern = r'fetch\(\s*[`"\']([^`"\']+)'

    for match in re.findall(fetch_pattern, code):
        fetches.append(match)

    return fetches


def extract_response_types(code: str):
    response_types = []

    for line in code.splitlines():
        stripped = line.strip()

        if "StreamingResponse" in stripped:
            response_types.append(stripped)

        elif "JSONResponse" in stripped:
            response_types.append(stripped)

        elif "Response(" in stripped:
            response_types.append(stripped)

        elif ".blob()" in stripped:
            response_types.append(stripped)

        elif ".json()" in stripped:
            response_types.append(stripped)

        elif "new Audio" in stripped:
            response_types.append(stripped)

        elif ".play(" in stripped:
            response_types.append(stripped)

        elif "createObjectURL" in stripped:
            response_types.append(stripped)

    return response_types


def build_flow_map(files):
    flow_lines = []
    all_routes = []
    all_fetches = []

    for item in files:
        path = item["file_path"]
        code = item["code"]

        routes = extract_routes(code)
        fetches = extract_fetches(code)
        responses = extract_response_types(code)

        flow_lines.append(f"\nFILE: {path}")

        if routes:
            flow_lines.append("BACKEND_ROUTES:")
            for route in routes:
                flow_lines.append(
                    f"- {route['method']} {route['path']} -> {route['handler']}"
                )
                all_routes.append((path, route))

        if fetches:
            flow_lines.append("FRONTEND_FETCHES:")
            for fetch_url in fetches:
                flow_lines.append(f"- fetch({fetch_url})")
                all_fetches.append((path, fetch_url))

        if responses:
            flow_lines.append("RESPONSE_AND_AUDIO_HANDLING:")
            for response in responses:
                flow_lines.append(f"- {response}")

        important_lines = []

        for line in code.splitlines():
            stripped = line.strip()

            if (
                stripped.startswith("def ")
                or stripped.startswith("async def ")
                or stripped.startswith("function ")
                or ".onclick" in stripped
                or "addEventListener" in stripped
                or "text_to_speech" in stripped
                or "audio" in stripped.lower()
                or "tts" in stripped.lower()
            ):
                important_lines.append(stripped)

        if important_lines:
            flow_lines.append("IMPORTANT_FLOW_LINES:")
            for line in important_lines[:40]:
                flow_lines.append(f"- {line}")

    if all_routes or all_fetches:
        flow_lines.append("\nCROSS_FILE_CONNECTIONS:")

        if all_fetches and all_routes:
            for fetch_file, fetch_url in all_fetches:
                matched = False

                for route_file, route in all_routes:
                    route_path = route["path"]

                    if (
                        fetch_url.endswith(route_path)
                        or route_path in fetch_url
                        or fetch_url in route_path
                    ):
                        flow_lines.append(
                            f"- {fetch_file} fetch({fetch_url}) likely connects to "
                            f"{route_file} {route['method']} {route_path}"
                        )
                        matched = True

                if not matched:
                    flow_lines.append(
                        f"- {fetch_file} fetch({fetch_url}) has no obvious matching route in checked files."
                    )

        elif all_fetches:
            for fetch_file, fetch_url in all_fetches:
                flow_lines.append(
                    f"- {fetch_file} fetch({fetch_url}) found, but no backend routes were checked."
                )

        elif all_routes:
            for route_file, route in all_routes:
                flow_lines.append(
                    f"- {route_file} route {route['method']} {route['path']} found, but no frontend fetches were checked."
                )

    return "\n".join(flow_lines)

def get_related_files(context, target_files):
    graph = context.get("relationship_graph", {})
    links = graph.get("fetch_to_route", [])

    related = set()

    normalized_targets = {
        file.replace("\\", "/").strip().lower()
        for file in target_files
    }

    for link in links:
        frontend = link["frontend_file"].replace("\\", "/").lower()
        backend = link["backend_file"].replace("\\", "/").lower()

        if frontend in normalized_targets:
            related.add(link["backend_file"])

        if backend in normalized_targets:
            related.add(link["frontend_file"])

    return list(related)

def check(files: list[str] = typer.Argument(None)):
    context = load_context()

    if not context:
        console.print(
            "[red]No debugging context found.[/red]\n"
            "Run vibe complain first 😭"
        )
        return

    if files is None:
        files = []

    if not files:
        files = context.get("suggested_files", [])

        if not files:
            console.print(
                "[red]No files provided and no suggested files found.[/red]\n"
                "Run vibe check app.py index.html or run vibe complain again."
            )
            return

    files = dedupe_files(files)
    related_files = get_related_files(context, files)

    for related in related_files:
        if related not in files:
            files.append(related)
    files = dedupe_files(files) 
    loaded_files = []
    seen_resolved_paths = set()

    for file in files:
        resolved, matches = resolve_file(file)

        if matches:
            console.print(f"[yellow]Multiple matches for {file}:[/yellow]")

            for match in matches:
                console.print(f"- {match}")

            continue

        if not resolved:
            console.print(f"[red]Could not find file:[/red] {file}")
            continue

        resolved_key = str(resolved).replace("\\", "/")

        if resolved_key in seen_resolved_paths:
            continue

        seen_resolved_paths.add(resolved_key)

        code, error = read_text_file(str(resolved))

        if error:
            console.print(f"[red]{error}[/red]")
            continue

        symbol_ranges = get_symbol_ranges_for_file(
            context,
            str(resolved),
        )

        smart_code = build_smart_context(
            code,
            str(resolved),
            context.get("complaint", ""),
            symbol_ranges=symbol_ranges,
        )

        console.print(f"[cyan]Loaded:[/cyan] {resolved}")

        if smart_code != code:
            console.print(
                f"[dim]Trimmed smart context for token limit:[/dim] {resolved}"
            )

        loaded_files.append({
            "file_path": str(resolved),
            "code": smart_code,
        })

    if not loaded_files:
        console.print("[red]No readable files found.[/red]")
        return

    files_blob = "\n\n".join(
        f"--- FILE: {item['file_path']} ---\n{item['code']}"
        for item in loaded_files
    )

    flow_map = build_flow_map(loaded_files)

    console.print(
        f"[cyan]Checking {len(loaded_files)} file(s) together...[/cyan]"
    )

    try:
        cache_key = make_hash(
            "check",
            context.get("complaint", ""),
            files_blob,
            flow_map,
        )

        cached = get_cache(cache_key)

        if cached:
            answer = cached.get("answer")
            console.print("[green]Using cached check result.[/green]")
        else:
            answer = ask_ai(
                MULTI_CHECK_PROMPT.format(
                    complaint=context.get("complaint", ""),
                    logs=context.get("logs", "No logs provided."),
                    tree=context.get("tree", ""),
                    flow_map=flow_map,
                    files=files_blob,
                )
            )

            if answer and not answer.startswith("AI Error:"):
                set_cache(cache_key, {"answer": answer})

        if not answer or answer.startswith("AI Error:"):
            console.print(
                Panel(
                    answer or "No AI response.",
                    title="🕵️ Vibe Multi-File Check",
                    border_style="red",
                )
            )
            console.print("[yellow]Check results were not saved.[/yellow]")
            return

        relevance_scores = extract_relevance_scores(answer)

        checks = []

        for item in loaded_files:
            score = find_score_for_file(
                relevance_scores,
                item["file_path"],
            )

            checks.append({
                "complaint": context.get("complaint", ""),
                "file_path": item["file_path"],
                "analysis": answer,
                "relevance_score": score,
            })

        update_context({
            "last_check": checks[-1],
            "checks": checks,
            "multi_check_analysis": answer,
        })

        console.print(
            Panel(
                answer,
                title="🕵️ Vibe Multi-File Check",
                border_style="cyan",
            )
        )

        console.print(
            f"[green]Saved {len(checks)} check result(s) to context.[/green]"
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")