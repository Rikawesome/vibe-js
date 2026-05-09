from rich.console import Console
from rich.panel import Panel

from vibe.prompts.prompts import COMPLAIN_PROMPT
from vibe.services.ai import ask_ai
from vibe.services.tree import build_tree
from vibe.services.context import save_context

console = Console()


def complain(complaint: str):
    console.print("[cyan]Listening to your suffering...[/cyan]")
    console.print("[cyan]Scanning project shape...[/cyan]")

    try:
        tree = build_tree(".", max_depth=3)
        save_context({
    "complaint": complaint,
    "tree": tree,
})

        answer = ask_ai(
            COMPLAIN_PROMPT.format(
                complaint=complaint,
                tree=tree,
            )
        )

        console.print(
            Panel(
                answer,
                title="😭 Vibe Complain",
                border_style="magenta",
            )
        )

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")