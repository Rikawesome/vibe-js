import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
def doctor():
    table = Table(title="🩺 Vibe Doctor")

    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")

    checks = {
        "package.json": Path("package.json").exists(),
        ".env": Path(".env").exists(),
        "node_modules": Path("node_modules").exists(),
        ".git": Path(".git").exists(),
    }

    for item, status in checks.items():
        table.add_row(item, "✅ Found" if status else "❌ Missing")

    console.print(table)

    package_path = Path("package.json")

    if package_path.exists():
        try:
            package_data = json.loads(package_path.read_text(encoding="utf-8"))

            scripts = package_data.get("scripts", {})
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})

            console.print("\n[bold cyan]📦 Project Info[/bold cyan]")
            console.print(f"Name: {package_data.get('name', 'Unknown')}")
            console.print(f"Scripts: {', '.join(scripts.keys()) or 'None'}")

            all_deps = {**dependencies, **dev_dependencies}

            if "next" in all_deps:
                console.print("Framework: Next.js detected ⚡")
            elif "vite" in all_deps:
                console.print("Framework: Vite detected ⚡")
            elif "react" in all_deps:
                console.print("Framework: React detected ⚛️")
            elif "express" in all_deps:
                console.print("Framework: Express detected 🚂")
            else:
                console.print("Framework: Unknown. This project is moving suspiciously.")

        except Exception as e:
            console.print(f"[red]Could not read package.json:[/red] {e}")

    if checks["package.json"] and not checks["node_modules"]:
        console.print("[yellow]Recommendation:[/yellow] Run npm install 😭")

    if not checks["package.json"]:
        console.print("\n[red]Diagnosis:[/red] This does not look like a JS project 😭")
