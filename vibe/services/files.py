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


def apply_patches(content: str, patch_text: str):
    patches = []
    current_find = None
    current_replace = None
    mode = None

    for line in patch_text.splitlines():
        if line.strip() == "--- PATCH ---":
            current_find = []
            current_replace = []
            mode = None
            continue

        if line.strip() == "FIND:":
            mode = "find"
            continue

        if line.strip() == "REPLACE:":
            mode = "replace"
            continue

        if line.strip() == "--- END PATCH ---":
            find_text = "\n".join(current_find).strip("\n")
            replace_text = "\n".join(current_replace).strip("\n")
            patches.append((find_text, replace_text))
            current_find = None
            current_replace = None
            mode = None
            continue

        if mode == "find" and current_find is not None:
            current_find.append(line)
        elif mode == "replace" and current_replace is not None:
            current_replace.append(line)

    updated = content
    applied = 0
    failed = []

    for find_text, replace_text in patches:
        if find_text in updated:
            updated = updated.replace(find_text, replace_text, 1)
            applied += 1
        else:
            failed.append(find_text[:120])

    return updated, applied, failed