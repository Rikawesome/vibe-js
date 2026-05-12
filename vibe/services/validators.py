import ast
import subprocess
import tempfile
from pathlib import Path


def validate_python(code: str):
    try:
        ast.parse(code)
        return True, "Python syntax OK."
    except SyntaxError as e:
        return False, f"{e.msg} on line {e.lineno}"


def validate_javascript(code: str):
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".js",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as temp:
            temp.write(code)
            temp_path = temp.name

        result = subprocess.run(
            ["node", "--check", temp_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        Path(temp_path).unlink(missing_ok=True)

        if result.returncode == 0:
            return True, "JavaScript syntax OK."

        return False, result.stderr.strip() or "JavaScript syntax error."

    except FileNotFoundError:
        return True, "Node.js not installed, skipped JavaScript syntax check."

    except Exception as e:
        return False, str(e)


def validate_code(file_path: str, code: str):
    lowered = file_path.lower()

    if lowered.endswith(".py"):
        return validate_python(code)

    if lowered.endswith(".js"):
        return validate_javascript(code)

    return True, "No local validator for this file type."