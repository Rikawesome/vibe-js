from pathlib import Path

IGNORE_DIRS = {"venv", ".git", "__pycache__", "node_modules", ".pytest_cache"}


def build_tree(root: str = ".", max_depth: int = 3) -> str:
    root_path = Path(root)
    lines = [f"{root_path.resolve().name}/"]

    def walk(path: Path, prefix: str = "", depth: int = 0):
        if depth >= max_depth:
            return

        try:
            items = sorted(
                [p for p in path.iterdir() if p.name not in IGNORE_DIRS],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            return

        for index, item in enumerate(items):
            connector = "└── " if index == len(items) - 1 else "├── "
            suffix = "/" if item.is_dir() else ""
            lines.append(f"{prefix}{connector}{item.name}{suffix}")

            if item.is_dir():
                extension = "    " if index == len(items) - 1 else "│   "
                walk(item, prefix + extension, depth + 1)

    walk(root_path)
    return "\n".join(lines)