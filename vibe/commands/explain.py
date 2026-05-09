from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import EXPLAIN_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file

console = Console()


def explain(file: str):
    resolved, matches = resolve_file(file)

    if matches:
        console.print("[yellow]Multiple matching files found:[/yellow]")
        for match in matches:
            console.print(f"- {match}")
        return

    if not resolved:
        console.print(f"[red]Could not find file:[/red] {file}")
        return

    console.print(f"[cyan]Reading:[/cyan] {resolved}")

    code, error = read_text_file(str(resolved))

    if error:
        console.print(f"[red]{error}[/red]")
        return

    console.print("[blue]Preparing explanation...[/blue]")

    try:
        answer = ask_ai(EXPLAIN_PROMPT.format(code=code))

        console.print(
            Panel(
                answer,
                title="🧠 Vibe Explain",
                border_style="blue",
            )
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")