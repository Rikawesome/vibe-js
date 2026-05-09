import subprocess


def run_git(args):
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def get_staged_diff():
    result = run_git(["diff", "--cached"])
    return result.stdout or ""


def fallback_commit_message():
    result = run_git(["diff", "--cached", "--name-only"])
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    if not files:
        return "update project files"

    if len(files) == 1:
        return f"update {files[0]}"

    return f"update {len(files)} project files"