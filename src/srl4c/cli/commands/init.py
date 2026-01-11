"""Init command - setup ~/.srl4c/ directory"""

import shutil

import yaml
from rich.console import Console

from srl4c.paths import TEMPLATES_DIR, USER_CONFIG_DIR


def run_init(console: Console):
    """Initialize SRL4C directory structure"""
    console.print("\n[bold]Welcome to SRL4C[/bold] - Safety Readiness Level for Children\n")

    # Create directories
    dirs = [
        USER_CONFIG_DIR,
        USER_CONFIG_DIR / "datasets",
        USER_CONFIG_DIR / "principles",
    ]

    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True)
            console.print(f"  [green]✓[/green] Created {d}")
        else:
            console.print(f"  [dim]✓ Exists {d}[/dim]")

    # Copy template files if they don't exist
    templates = ["weights.yaml", "guardrails.yaml"]
    for template in templates:
        src = TEMPLATES_DIR / template
        dst = USER_CONFIG_DIR / template
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            console.print(f"  [green]✓[/green] Created {dst}")
        elif dst.exists():
            console.print(f"  [dim]✓ Exists {dst}[/dim]")

    # Copy judge config files (.judges)
    judge_files = ["default.judges", "fake.judges"]
    for jf in judge_files:
        src = TEMPLATES_DIR / jf
        dst = USER_CONFIG_DIR / jf
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            console.print(f"  [green]✓[/green] Created {dst}")
        elif dst.exists():
            console.print(f"  [dim]✓ Exists {dst}[/dim]")

    # Create settings.yaml with default judge selection
    settings_path = USER_CONFIG_DIR / "settings.yaml"
    if not settings_path.exists():
        settings = {"active_judges": "default.judges"}
        with open(settings_path, "w") as f:
            yaml.dump(settings, f)
        console.print(f"  [green]✓[/green] Created {settings_path}")
    else:
        console.print(f"  [dim]✓ Exists {settings_path}[/dim]")

    console.print("\n[green]Setup complete![/green]\n")
    console.print("Judge configs available in [cyan]~/.srl4c/*.judges[/cyan]")
    console.print("Add judge API keys to [cyan].env[/cyan] (copy from .env.example)\n")
    console.print("Next steps:")
    console.print("  [cyan]srl4c judges list[/cyan]            # See available judge configs")
    console.print("  [cyan]srl4c judges use <name>[/cyan]      # Switch judge config")
    console.print("  [cyan]srl4c endpoint add --help[/cyan]   # Configure an endpoint")
    console.print("  [cyan]srl4c dataset list[/cyan]          # See available datasets\n")
