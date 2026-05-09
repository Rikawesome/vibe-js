from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import CHECK_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.context import load_context,update_context
from vibe.services.files import read_text_file
from vibe.services.resolver import resolve_file

console = Console()


def check(files: list[str]):
    context = load_context()

    if not context:
        console.print(
            "[red]No debugging context found.[/red]\n"
            "Run vibe complain first 😭"
        )
        return

    all_checks = []

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

        code, error = read_text_file(str(resolved))

        if error:
            console.print(f"[red]{error}[/red]")
            continue

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

            all_checks.append({
                "complaint": context["complaint"],
                "file_path": str(resolved),
                "analysis": answer,
            })

            console.print(
                Panel(
                    answer,
                    title=f"🕵️ Vibe Check: {resolved}",
                    border_style="cyan",
                )
            )

        except Exception as e:
            console.print(f"[red]AI Error:[/red] {e}")

    if all_checks:
        update_context({
            "last_check": all_checks[-1],
            "checks": all_checks,
        })

        console.print(
            f"[green]Saved {len(all_checks)} check result(s) to context.[/green]"
        )