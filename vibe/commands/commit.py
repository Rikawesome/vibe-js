import subprocess

from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import COMMIT_PROMPT
from vibe.services.ai import ask_ai

console = Console()


def commit():
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        diff = result.stdout or ""

        if not diff.strip():
            console.print("[yellow]No staged changes found.[/yellow]")
            return

        console.print("[cyan]Analyzing git diff...[/cyan]")

        answer = ask_ai(COMMIT_PROMPT.format(diff=diff))

        console.print(
            Panel(
                answer,
                title="📝 Vibe Commit",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Git Error:[/red] {e}")