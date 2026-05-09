from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import COMMIT_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.git import get_staged_diff, fallback_commit_message

console = Console()


def commit():
    diff = get_staged_diff()

    if not diff.strip():
        console.print("[yellow]No staged changes found.[/yellow]")
        return

    console.print("[cyan]Analyzing git diff...[/cyan]")

    answer = ask_ai(COMMIT_PROMPT.format(diff=diff))

    if answer.startswith("AI Error:"):
        answer = fallback_commit_message()
        console.print("[yellow]AI unavailable. Using fallback commit message.[/yellow]")

    console.print(
        Panel(
            answer,
            title="📝 Vibe Commit",
            border_style="green",
        )
    )