from rich.console import Console

console = Console()

VERSION = "0.1.0"


def version():
    console.print(f"[bold cyan]Vibe JS[/bold cyan] v{VERSION} 😭")