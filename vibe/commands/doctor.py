import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def mask_key(value: str):
    if not value:
        return "missing"

    if len(value) <= 8:
        return "set"

    return f"{value[:4]}...{value[-4:]}"


def count_cache_files():
    cache_dir = Path(".vibe") / "cache"

    if not cache_dir.exists():
        return 0

    return len(list(cache_dir.glob("*.json")))


def doctor():
    load_dotenv()

    provider = os.getenv("VIBE_PROVIDER", "auto")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    table = Table(title="🩺 Vibe Doctor")

    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Notes")

    table.add_row("VIBE_PROVIDER", provider, "auto, gemini, or groq")
    table.add_row("GEMINI_API_KEY / GOOGLE_API_KEY", mask_key(gemini_key), "Gemini provider")
    table.add_row("GROQ_API_KEY", mask_key(groq_key), "Groq fallback/provider")

    node_path = shutil.which("node")
    table.add_row(
        "Node.js",
        "found" if node_path else "missing",
        node_path or "JS validation will be skipped",
    )

    table.add_row(
        "Cache",
        f"{count_cache_files()} file(s)",
        ".vibe/cache",
    )

    context_file = Path(".vibe") / "context.json"
    table.add_row(
        "Context",
        "found" if context_file.exists() else "missing",
        str(context_file),
    )

    console.print(table)

    if provider == "groq" and not groq_key:
        console.print(
            Panel(
                "VIBE_PROVIDER is set to groq, but GROQ_API_KEY is missing.",
                title="Problem Found",
                border_style="red",
            )
        )

    if provider == "gemini" and not gemini_key:
        console.print(
            Panel(
                "VIBE_PROVIDER is set to gemini, but GEMINI_API_KEY/GOOGLE_API_KEY is missing.",
                title="Problem Found",
                border_style="red",
            )
        )

    if provider == "auto" and not gemini_key and not groq_key:
        console.print(
            Panel(
                "No AI keys found. Add GEMINI_API_KEY or GROQ_API_KEY to .env.",
                title="Problem Found",
                border_style="red",
            )
        )