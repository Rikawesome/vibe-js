from rich.console import Console
from rich.panel import Panel

from vibe.services.git import run_git, get_staged_diff, fallback_commit_message
from vibe.prompts.prompts import COMMIT_PROMPT
from vibe.services.ai import ask_ai

console = Console()


def sync():
    console.print("[cyan]Staging changes...[/cyan]")
    add_result = run_git(["add", "."])

    if add_result.returncode != 0:
        console.print(f"[red]Git add failed:[/red]\n{add_result.stderr}")
        return

    diff = get_staged_diff()

    if not diff.strip():
        console.print("[yellow]No changes to sync.[/yellow]")
        return

    console.print("[cyan]Generating commit message...[/cyan]")
    message = ask_ai(COMMIT_PROMPT.format(diff=diff))

    if message.startswith("AI Error:"):
        message = fallback_commit_message()
        console.print("[yellow]AI unavailable. Using fallback commit message.[/yellow]")

    console.print(
        Panel(
            message,
            title="📝 Commit Message",
            border_style="green",
        )
    )

    console.print("[cyan]Committing changes...[/cyan]")
    commit_result = run_git(["commit", "-m", message])

    if commit_result.returncode != 0:
        console.print(f"[red]Git commit failed:[/red]\n{commit_result.stderr}")
        return

    console.print("[cyan]Pushing to remote...[/cyan]")
    push_result = run_git(["push"])

    if push_result.returncode != 0:
        console.print(f"[red]Git push failed:[/red]\n{push_result.stderr}")
        return

    console.print("[green]Vibe sync complete. Shipped successfully 😭[/green]")