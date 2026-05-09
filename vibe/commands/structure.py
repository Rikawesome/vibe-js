from pathlib import Path

from rich.console import Console
from rich.tree import Tree

console = Console()


def get_depth(line: str) -> int:
    depth = 0

    while line.startswith("│   ") or line.startswith("    "):
        depth += 1
        line = line[4:]

    return depth


def clean_line(line: str) -> str:
    line = line.strip()

    # Remove tree branch symbols
    line = line.replace("├──", "")
    line = line.replace("└──", "")

    # Remove leftover vertical tree pipes
    line = line.replace("│", "")

    return line.strip()


def structure(file: str):
    path = Path(file)

    if not path.exists():
        console.print(f"[red]Structure file not found:[/red] {file}")
        return

    lines = path.read_text(encoding="utf-8").splitlines()

    stack = []
    created = []

    for raw_line in lines:
        if not raw_line.strip():
            continue

        depth = get_depth(raw_line)
        name = clean_line(raw_line)

        while len(stack) > depth + 1:
            stack.pop()

        current_path = Path(*stack) / name.rstrip("/")

        if name.endswith("/"):
            current_path.mkdir(parents=True, exist_ok=True)
            created.append(f"📂 {current_path}")
            stack.append(name.rstrip("/"))
        else:
            current_path.parent.mkdir(parents=True, exist_ok=True)
            current_path.touch(exist_ok=True)
            created.append(f"📄 {current_path}")

    tree = Tree("🏗️ Generated Structure")

    for item in created:
        tree.add(item)

    console.print("[green]Structure created successfully![/green]")
    console.print(tree)