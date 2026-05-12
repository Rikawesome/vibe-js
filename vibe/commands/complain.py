from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import COMPLAIN_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.tree import build_tree
from vibe.services.context import save_context, extract_file_paths
from vibe.services.project_index import (
    build_project_index,
    format_project_index,
)
from vibe.services.graph import build_relationship_graph

console = Console()


def complain():
    console.print("[bold cyan]😭 Vibe Complain[/bold cyan]\n")

    complaint = console.input(
        "[cyan]What’s wrong?[/cyan]\n> "
    ).strip()

    console.print(
        "\n[yellow]Paste terminal logs below.[/yellow]"
    )
    console.print(
        "[dim]Type END on a new line when done. "
        "Press ENTER immediately to skip.[/dim]\n"
    )

    log_lines = []

    while True:
        line = input()

        if line.strip() == "END":
            break

        if not line.strip() and not log_lines:
            break

        log_lines.append(line)

    logs_text = "\n".join(log_lines)

    console.print("\n[cyan]Listening to your suffering...[/cyan]")
    console.print("[cyan]Scanning project shape...[/cyan]")

    try:
        tree = build_tree(".", max_depth=3)
        console.print("[cyan]Indexing project symbols...[/cyan]")

        project_symbols = build_project_index(".")
        project_index = format_project_index(project_symbols)
        relationship_graph = build_relationship_graph(project_symbols)

        answer = ask_ai(
            COMPLAIN_PROMPT.format(
                complaint=complaint,
                logs=logs_text or "No logs provided.",
                tree=tree,
                project_index=project_index,
            )
        )

        suggested_files = extract_file_paths(answer)

        save_context({
            "complaint": complaint,
            "logs": logs_text,
            "tree": tree,
            "suggested_files": suggested_files,
            "project_symbols": project_symbols,
            "project_index": project_index,
            "relationship_graph": relationship_graph,
        })

        console.print(
            Panel(
                answer,
                title="😭 Vibe Complain",
                border_style="magenta",
            )
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")