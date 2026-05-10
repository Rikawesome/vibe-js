from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import COMPLAIN_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.tree import build_tree
from vibe.services.context import save_context, extract_file_paths

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

        answer = ask_ai(
            COMPLAIN_PROMPT.format(
                complaint=complaint,
                logs=logs_text or "No logs provided.",
                tree=tree,
            )
        )

        suggested_files = extract_file_paths(answer)

        save_context({
            "complaint": complaint,
            "logs": logs_text,
            "tree": tree,
            "suggested_files": suggested_files,
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