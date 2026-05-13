import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()


IMPORT_ALIASES = {
    "dotenv": "python-dotenv",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "jwt": "PyJWT",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "edge_tts": "edge-tts",
}


IGNORE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
}


def should_skip(path: Path):
    return any(part in IGNORE_DIRS for part in path.parts)


def file_exists(name: str):
    return Path(name).exists()


def run_command(command: list[str]):
    console.print(f"[green]Running:[/green] {' '.join(command)}")
    subprocess.run(command)


def package_installed(import_name: str):
    return importlib.util.find_spec(import_name) is not None


def is_stdlib(import_name: str):
    root_name = import_name.split(".")[0]

    if root_name in sys.builtin_module_names:
        return True

    if hasattr(sys, "stdlib_module_names"):
        return root_name in sys.stdlib_module_names

    return False


def is_local_module(import_name: str):
    root_name = import_name.split(".")[0]

    return (
        Path(f"{root_name}.py").exists()
        or Path(root_name).is_dir()
    )


def extract_imports_from_file(path: Path):
    imports = set()

    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def scan_python_imports():
    imports = set()

    for path in Path(".").rglob("*.py"):
        if should_skip(path):
            continue

        imports.update(extract_imports_from_file(path))

    return imports


def infer_package_name(import_name: str):
    return IMPORT_ALIASES.get(import_name, import_name)


def install_python_packages(packages: list[str]):
    if not packages:
        return

    console.print("[yellow]Missing Python packages detected:[/yellow]")

    for package in packages:
        console.print(f"- {package}")

    console.print("[cyan]Installing packages...[/cyan]")

    subprocess.run([
        sys.executable,
        "-m",
        "pip",
        "install",
        *packages,
    ])


def install_requirements_if_present():
    if file_exists("requirements.txt"):
        console.print("[cyan]Installing from requirements.txt...[/cyan]")
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
        ])


def auto_install_missing_python_packages():
    install_requirements_if_present()

    imports = scan_python_imports()
    missing = []

    for import_name in imports:
        if is_stdlib(import_name):
            continue

        if is_local_module(import_name):
            continue

        if package_installed(import_name):
            continue

        missing.append(infer_package_name(import_name))

    install_python_packages(sorted(set(missing)))


def detect_python_app():
    candidates = ["main.py", "app.py"]

    for filename in candidates:
        path = Path(filename)

        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8", errors="ignore")
        module = path.stem

        if "FastAPI" in content:
            return "FastAPI", ["uvicorn", f"{module}:app", "--reload"]

        if "Flask" in content:
            return "Flask", ["flask", "--app", module, "run", "--debug"]

    return None, None


def read_package_json():
    try:
        return json.loads(
            Path("package.json").read_text(encoding="utf-8")
        )
    except Exception:
        return {}


def install_node_packages_if_needed():
    if not file_exists("package.json"):
        return

    if Path("node_modules").exists():
        return

    console.print("[cyan]node_modules missing. Running npm install...[/cyan]")
    subprocess.run(["npm", "install"])


def detect_node_command():
    package_json = read_package_json()
    scripts = package_json.get("scripts", {})

    if "dev" in scripts:
        return ["npm", "run", "dev"]

    if "start" in scripts:
        return ["npm", "start"]

    return None


def run():
    if file_exists("package.json"):
        console.print("[cyan]Detected Node project[/cyan]")
        install_node_packages_if_needed()

        command = detect_node_command()

        if command:
            run_command(command)
            return

        console.print("[red]No npm dev/start script found.[/red]")
        return

    app_type, command = detect_python_app()

    if app_type:
        console.print(f"[cyan]Detected {app_type} project[/cyan]")
        auto_install_missing_python_packages()
        run_command(command)
        return

    console.print("[red]Could not detect how to run this project.[/red]")
    console.print("Try manually: uvicorn main:app --reload")