"""Init command - setup ~/.srl4c/ directory"""

import shutil
from pathlib import Path

from rich.console import Console


SRL4C_HOME = Path.home() / ".srl4c"
SRL4C_ROOT = Path(__file__).parent.parent.parent.parent.parent  # srl4c/
TEMPLATES_DIR = SRL4C_ROOT / "templates"


def run_init(console: Console):
    """Initialize SRL4C directory structure"""
    console.print("\n[bold]Welcome to SRL4C[/bold] - Safety Readiness Level for Children\n")

    # Create directories
    dirs = [
        SRL4C_HOME,
        SRL4C_HOME / "datasets",
        SRL4C_HOME / "principles",
    ]

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True)
            console.print(f"  [green]✓[/green] Created {d}")
        else:
            console.print(f"  [dim]✓ Exists {d}[/dim]")

    # Copy judges.yaml template if it doesn't exist
    judges_src = TEMPLATES_DIR / "judges.yaml"
    judges_dst = SRL4C_HOME / "judges.yaml"
    if judges_src.exists() and not judges_dst.exists():
        shutil.copy(judges_src, judges_dst)
        console.print(f"  [green]✓[/green] Created {judges_dst}")
    elif judges_dst.exists():
        console.print(f"  [dim]✓ Exists {judges_dst}[/dim]")

    console.print("\n[green]Setup complete![/green]\n")
    console.print("Configure judges in [cyan]~/.srl4c/judges.yaml[/cyan]")
    console.print("Add judge API keys to [cyan]srl4c/.env[/cyan] (copy from .env.example)\n")
    console.print("Next steps:")
    console.print("  [cyan]srl4c endpoint add --help[/cyan]   # Configure an endpoint")
    console.print("  [cyan]srl4c dataset list[/cyan]          # See available datasets")
    console.print("  [cyan]srl4c principles list[/cyan]       # See evaluation principles\n")
