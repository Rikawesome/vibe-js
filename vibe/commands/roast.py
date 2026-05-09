from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import ROAST_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file

console = Console()


def roast(file: str):
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

    console.print("[red]Preparing roast...[/red]")

    try:
        answer = ask_ai(ROAST_PROMPT.format(code=code))

        console.print(
            Panel(
                answer,
                title="🔥 Vibe Roast",
                border_style="red",
            )
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")