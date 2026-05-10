from rich.console import Console
from rich.panel import Panel
import typer

from vibe.prompts.prompts import (
    FIX_PROMPT,
    PATCH_FIX_PROMPT,
    PATCH_VALIDATE_PROMPT,
)
from vibe.services.ai import ask_ai
from vibe.services.context import (
    load_context,
    find_checks_by_keywords,
)
from vibe.services.files import (
    read_text_file,
    write_text_file,
    backup_file,
    apply_patches,
)

console = Console()


def fix_one(file: str, selected_check, context, write: bool):
    code, error = read_text_file(file)

    if error:
        console.print(f"[red]{error}[/red]")
        return

    console.print(f"[cyan]Thinking of a safer version for:[/cyan] {file}")

    try:
        patch_response = None

        if selected_check:
            patch_response = ask_ai(
                PATCH_FIX_PROMPT.format(
                    complaint=selected_check.get(
                        "complaint",
                        context.get("complaint", ""),
                    ),
                    file_path=selected_check["file_path"],
                    analysis=selected_check["analysis"],
                    code=code,
                )
            )

            if patch_response and patch_response.strip() == "NO_PATCHES":
                console.print("[yellow]No patches needed for this file.[/yellow]")
                return

            if not patch_response or patch_response.startswith("AI Error:"):
                console.print(f"[red]AI failed:[/red] {patch_response}")
                console.print("[yellow]File was not changed.[/yellow]")
                return

            improved_code, applied, failed = apply_patches(code, patch_response)
            validation = ask_ai(
                PATCH_VALIDATE_PROMPT.format(
                    complaint=selected_check.get("complaint", context.get("complaint", "")),
                    file_path=selected_check["file_path"],
                    patch=patch_response,
                    code=improved_code,
                )
            )

            if not validation or validation.startswith("AI Error:"):
                console.print(f"[red]Validation failed:[/red] {validation}")
                console.print("[yellow]File was not changed.[/yellow]")
                return

            if not validation.strip().startswith("VALID"):
                console.print(f"[red]Patch rejected:[/red] {validation}")
                console.print("[yellow]File was not changed.[/yellow]")
                return

            console.print(f"[green]Applied {applied} patch(es).[/green]")

            if failed:
                console.print(
                    f"[yellow]{len(failed)} patch(es) failed to match exactly.[/yellow]"
                )

        else:
            improved_code = ask_ai(FIX_PROMPT.format(code=code))

            if not improved_code or improved_code.startswith("AI Error:"):
                console.print(f"[red]AI failed:[/red] {improved_code}")
                console.print("[yellow]File was not changed.[/yellow]")
                return

        if write:
            backup_path = backup_file(file)
            error = write_text_file(file, improved_code)

            if error:
                console.print(f"[red]Write Error:[/red] {error}")
                return

            console.print(
                f"[green]Updated:[/green] {file}\n"
                f"Backup created: {backup_path}"
            )
        else:
            preview_content = patch_response if selected_check else improved_code

            console.print(
                Panel(
                    preview_content,
                    title=f"🛠️ Vibe Fix Preview: {file}",
                    border_style="yellow",
                )
            )

            console.print("\n[yellow]Preview only.[/yellow] No files were changed.")

    except Exception as e:
        console.print(f"[red]AI Error:[/red] {e}")


def fix(
    target: str = typer.Argument(None),
    write: bool = False,
    last_check: bool = False,
):
    context = load_context()

    if last_check:
        if not context or "last_check" not in context:
            console.print("[red]No last check found.[/red] Run vibe check first 😭")
            return

        selected_check = context["last_check"]
        fix_one(selected_check["file_path"], selected_check, context, write)
        return

    if not target:
        console.print("[red]No file or issue provided.[/red]")
        return

    matched_checks = find_checks_by_keywords(target)

    if matched_checks:
        unique_checks = []
        seen_files = set()

        for check in matched_checks:
            file_path = check["file_path"]
            normalized = file_path.replace("\\", "/").strip()

            if normalized in seen_files:
                continue

            seen_files.add(normalized)
            unique_checks.append(check)

        console.print(
            f"[cyan]Matched {len(unique_checks)} unique check result(s).[/cyan]"
        )

        for check in unique_checks:
            score = check.get("relevance_score", 0)

            if score < 0.5:
                console.print(
                    f"[dim]Skipping low relevance file "
                    f"({score:.2f}):[/dim] "
                    f"{check['file_path']}"
                )
                continue
            console.print(f"[cyan]Fixing from check:[/cyan] {check['file_path']}")
            fix_one(check["file_path"], check, context or {}, write)

        return

    fix_one(target, None, context or {}, write)