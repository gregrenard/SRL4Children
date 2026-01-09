"""Init command - setup ~/.srl4c/ directory"""

from pathlib import Path

from rich.console import Console


SRL4C_HOME = Path.home() / ".srl4c"


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

    # Create .env if not exists
    env_file = SRL4C_HOME / ".env"
    if not env_file.exists():
        env_file.write_text("# API keys for your endpoints\n# MYAPP_PROD_KEY=sk-...\n")
        console.print(f"  [green]✓[/green] Created {env_file}")
    else:
        console.print(f"  [dim]✓ Exists {env_file}[/dim]")

    # Create config.yaml if not exists
    config_file = SRL4C_HOME / "config.yaml"
    if not config_file.exists():
        config_file.write_text("""# SRL4C Configuration

weights:
  presets:
    balanced:
      safety: 0.35
      anthropomorphism: 0.20
      age: 0.15
      relevance: 0.15
      ethics: 0.15
    safety-focused:
      safety: 0.60
      anthropomorphism: 0.15
      age: 0.10
      relevance: 0.10
      ethics: 0.05

output:
  default_format: table
  colors: true
""")
        console.print(f"  [green]✓[/green] Created {config_file}")
    else:
        console.print(f"  [dim]✓ Exists {config_file}[/dim]")

    console.print("\n[green]Setup complete![/green]\n")
    console.print("Add your API keys to [cyan]~/.srl4c/.env[/cyan]:")
    console.print("  MYAPP_PROD_KEY=sk-...")
    console.print("  MYAPP_STAGING_KEY=sk-...\n")
    console.print("Next steps:")
    console.print("  [cyan]srl4c endpoint add --help[/cyan]   # Configure an endpoint")
    console.print("  [cyan]srl4c dataset list[/cyan]          # See available datasets")
    console.print("  [cyan]srl4c principles list[/cyan]       # See evaluation principles\n")
