from pathlib import Path

from rich.console import Console

console = Console()


def setup():
    env_path = Path(".env")

    console.print("[bold cyan]🔧 Vibe JS Setup[/bold cyan]\n")

    if env_path.exists():
        console.print("[yellow].env already exists.[/yellow]")
        return

    api_key = console.input(
        "[cyan]Enter your Gemini API key:[/cyan] "
    ).strip()

    if not api_key:
        console.print("[red]No API key provided.[/red]")
        return

    env_path.write_text(
        f"GEMINI_API_KEY={api_key}\n",
        encoding="utf-8",
    )

    console.print("[green]Setup complete 😭[/green]")
    console.print("[cyan].env file created successfully.[/cyan]")