from rich.console import Console
from rich.panel import Panel
from vibe.services.ai import ask_ai
from vibe.services.files import (
    read_text_file,
    write_text_file,
    backup_file,
)
import typer
from vibe.prompts.prompts import FIX_PROMPT, CONTEXT_FIX_PROMPT
from vibe.services.context import load_context

console = Console()


def fix(
    file: str = typer.Argument(None),
    write: bool = False,
    last_check: bool = False,
):
    context = load_context() if last_check else None

    if last_check:
        if not context or "last_check" not in context:
            console.print("[red]No last check found.[/red] Run vibe check first 😭")
            return

        file = context["last_check"]["file_path"]

    if not file:
        console.print("[red]No file provided.[/red] Use a file path or --last-check.")
        return
    code, error = read_text_file(file)

    if error:
        console.print(f"[red]{error}[/red]")
        return

    console.print("[cyan]Thinking of a safer version...[/cyan]")

    try:
        if last_check:
            improved_code = ask_ai(
                CONTEXT_FIX_PROMPT.format(
                    complaint=context.get("complaint", ""),
                    file_path=context["last_check"]["file_path"],
                    analysis=context["last_check"]["analysis"],
                    code=code,
                )
            )
        else:
            improved_code = ask_ai(FIX_PROMPT.format(code=code))

        if write:
            backup_path = backup_file(file)

            error = write_text_file(file, improved_code)

            if error:
                console.print(f"[red]Write Error:[/red] {error}")
                return

            console.print(
                f"[green]File updated successfully.[/green]\n"
                f"Backup created: {backup_path}"
            )

        else:
            console.print(
                Panel(
                    improved_code,
                    title="🛠️ Vibe Fix Preview",
                    border_style="yellow",
                )
            )

            console.print(
                "\n[yellow]Preview only.[/yellow] No files were changed."
            )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")