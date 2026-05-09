from pathlib import Path


def read_text_file(file: str):
    path = Path(file)

    if not path.exists():
        return None, f"File not found: {file}"

    try:
        return path.read_text(encoding="utf-8"), None
    except Exception as e:
        return None, f"Could not read file: {e}"
from pathlib import Path
import shutil


def backup_file(file: str):
    backup_path = f"{file}.bak"
    shutil.copy(file, backup_path)
    return backup_path


def write_text_file(file: str, content: str):
    path = Path(file)

    try:
        path.write_text(content, encoding="utf-8")
        return None
    except Exception as e:
        return str(e)