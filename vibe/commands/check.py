from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import CHECK_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.context import load_context,update_context
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file

console = Console()


def check(file: str):
    context = load_context()

    if not context:
        console.print(
            "[red]No debugging context found.[/red]\n"
            "Run vibe complain first 😭"
        )
        return

    resolved, matches = resolve_file(file)

    if matches:
        console.print("[yellow]Multiple matching files found:[/yellow]")

        for match in matches:
            console.print(f"- {match}")

        return

    if not resolved:
        console.print(f"[red]Could not find file:[/red] {file}")
        return

    code, error = read_text_file(str(resolved))

    if error:
        console.print(f"[red]{error}[/red]")
        return

    console.print(f"[cyan]Checking:[/cyan] {resolved}")

    try:
        answer = ask_ai(
            CHECK_PROMPT.format(
                complaint=context["complaint"],
                tree=context["tree"],
                file_path=resolved,
                code=code,
            )
        )

        update_context({
            "last_check": {
                "file_path": str(resolved),
                "analysis": answer,
            }
        })

        console.print(
            Panel(
                answer,
                title="🕵️ Vibe Check",
                border_style="cyan",
            )
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")