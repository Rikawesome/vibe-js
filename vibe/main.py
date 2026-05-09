import typer

from vibe.commands.blame import blame
from vibe.commands.explain import explain
from vibe.commands.roast import roast
from vibe.commands.commit import commit
from vibe.commands.doctor import doctor
from vibe.commands.fix import fix
from vibe.commands.create import create
from vibe.commands.structure import structure
from vibe.commands.complain import complain
from vibe.commands.check import check
from vibe.commands.version import version
from vibe.commands.sync import sync
from vibe.commands.setup import setup
app = typer.Typer()

commands = [
    blame,
    explain,
    roast,
    commit,
    doctor,
    fix,
    create,
    structure,
    complain,
    check,
    version,
    sync,
    setup,
]

for command in commands:
    app.command()(command)


if __name__ == "__main__":
    app()