from rich.console import Console
from rich.panel import Panel
import typer

from vibe.prompts.prompts import FIX_PROMPT, CONTEXT_FIX_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.context import (
    load_context,
    find_checks_by_keywords,
)
from vibe.services.files import (
    read_text_file,
    write_text_file,
    backup_file,
)

console = Console()


def fix_one(file: str, selected_check, context, write: bool):
    code, error = read_text_file(file)

    if error:
        console.print(f"[red]{error}[/red]")
        return

    console.print(f"[cyan]Thinking of a safer version for:[/cyan] {file}")

    try:
        if selected_check:
            improved_code = ask_ai(
                CONTEXT_FIX_PROMPT.format(
                    complaint=selected_check.get(
                        "complaint",
                        context.get("complaint", ""),
                    ),
                    file_path=selected_check["file_path"],
                    analysis=selected_check["analysis"],
                    code=code,
                )
            )
        else:
            improved_code = ask_ai(
                FIX_PROMPT.format(code=code)
            )
        if not improved_code or improved_code.startswith("AI Error:"):
            console.print(f"[red]AI failed:[/red] {improved_code}")
            console.print("[yellow]File was not changed.[/yellow]")
            return

        if write:
            backup_path = backup_file(file)

            error = write_text_file(file, improved_code)

            if error:
                console.print(
                    f"[red]Write Error:[/red] {error}"
                )
                return

            console.print(
                f"[green]Updated:[/green] {file}\n"
                f"Backup created: {backup_path}"
            )

        else:
            console.print(
                Panel(
                    improved_code,
                    title=f"🛠️ Vibe Fix Preview: {file}",
                    border_style="yellow",
                )
            )

            console.print(
                "\n[yellow]Preview only.[/yellow] "
                "No files were changed."
            )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")


def fix(
    target: str = typer.Argument(None),
    write: bool = False,
    last_check: bool = False,
):
    context = load_context()

    if last_check:
        if not context or "last_check" not in context:
            console.print(
                "[red]No last check found.[/red] "
                "Run vibe check first 😭"
            )
            return

        selected_check = context["last_check"]

        fix_one(
            selected_check["file_path"],
            selected_check,
            context,
            write,
        )

        return

    if not target:
        console.print(
            "[red]No file or issue provided.[/red]"
        )
        return

    matched_checks = find_checks_by_keywords(target)

    if matched_checks:
        console.print(
            f"[cyan]Matched "
            f"{len(matched_checks)} "
            f"check result(s).[/cyan]"
        )

        for check in matched_checks:
            console.print(
                f"[cyan]Fixing from check:[/cyan] "
                f"{check['file_path']}"
            )

            fix_one(
                check["file_path"],
                check,
                context or {},
                write,
            )

        return

    fix_one(
        target,
        None,
        context or {},
        write,
    )