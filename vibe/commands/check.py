from rich.console import Console
from rich.panel import Panel
import typer

from vibe.prompts.prompts import MULTI_CHECK_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.context import (
    load_context,
    update_context,
    extract_relevance_scores,
)
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file

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


def build_smart_context(code: str, file_path: str, complaint: str):
    if len(code) <= MAX_FILE_CHARS:
        return code

    complaint_words = [
        word.lower()
        for word in complaint.replace("_", " ").replace("-", " ").split()
        if len(word) >= 4
    ]

    useful_keywords = set(complaint_words)

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

    for index, line in enumerate(lines):
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in useful_keywords):
            start = max(0, index - 8)
            end = min(len(lines), index + 18)
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


def build_flow_map(files):
    flow_lines = []

    for item in files:
        path = item["file_path"]
        code = item["code"]

        flow_lines.append(f"\nFILE: {path}")

        for line in code.splitlines():
            stripped = line.strip()

            if (
                stripped.startswith("def ")
                or stripped.startswith("async def ")
                or stripped.startswith("function ")
                or "=>" in stripped
                or "fetch(" in stripped
                or "addEventListener" in stripped
                or ".onclick" in stripped
                or "StreamingResponse" in stripped
                or "Response(" in stripped
                or "text_to_speech" in stripped
                or "audio" in stripped.lower()
                or "play(" in stripped
                or "blob()" in stripped
                or "createObjectURL" in stripped
            ):
                flow_lines.append(f"- {stripped}")

    return "\n".join(flow_lines)


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

        smart_code = build_smart_context(
            code,
            str(resolved),
            context.get("complaint", ""),
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
        answer = ask_ai(
            MULTI_CHECK_PROMPT.format(
                complaint=context.get("complaint", ""),
                logs=context.get("logs", "No logs provided."),
                tree=context.get("tree", ""),
                flow_map=flow_map,
                files=files_blob,
            )
        )

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