import random
import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer()
console = Console()

blames = [
    "The issue is probably npm behaving spiritually again.",
    "You renamed something and forgot.",
    "Your environment variables are plotting against you.",
    "This project was working yesterday out of pure luck.",
    "Congratulations. You have angered TypeScript.",
]


@app.command()
def blame():
    result = random.choice(blames)

    console.print(
        Panel.fit(
            result,
            title="🔥 Vibe Blame",
            border_style="red",
        )
    )