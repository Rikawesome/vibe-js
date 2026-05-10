from pathlib import Path

from rich.console import Console

console = Console()


def setup():
    env_path = Path(".env")

    console.print("[bold cyan]🔧 Vibe JS Setup[/bold cyan]\n")

    api_key = console.input(
        "[cyan]Enter your Gemini API key:[/cyan] "
    ).strip()

    if not api_key:
        console.print("[red]No API key provided.[/red]")
        return

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")

        if "GEMINI_API_KEY=" in content:
            console.print("[yellow]GEMINI_API_KEY already exists in .env.[/yellow]")
            return

        with open(env_path, "a", encoding="utf-8") as file:
            file.write(f"\nGEMINI_API_KEY={api_key}\n")

        console.print("[green]GEMINI_API_KEY added to existing .env 😭[/green]")
        return

    env_path.write_text(
        f"GEMINI_API_KEY={api_key}\n",
        encoding="utf-8",
    )

    console.print("[green]Setup complete 😭[/green]")
    console.print("[cyan].env file created successfully.[/cyan]")