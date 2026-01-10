"""Dataset commands"""

import pandas as pd
from rich.console import Console
from rich.table import Table

from srl4c.core.datasets import get_all_datasets


def get_builtin_datasets() -> dict:
    """Get list of built-in datasets (wrapper for backwards compatibility)"""
    datasets = get_all_datasets()
    # Convert to old format for compatibility
    return {
        name: {
            "path": info["path"],
            "prompts": info["rows"],
            "principles": set(info["principles"]),
        }
        for name, info in datasets.items()
    }


def list_datasets(console: Console):
    """List available datasets"""
    datasets = get_builtin_datasets()

    console.print("\n[bold]BUILT-IN[/bold]")
    table = Table(show_edge=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Prompts", justify="right", no_wrap=True)
    table.add_column("Principles", no_wrap=True)

    for name, info in sorted(datasets.items()):
        principles_str = f"{len(info['principles'])} principles" if info['principles'] else "—"
        table.add_row(name, str(info["prompts"]), principles_str)

    console.print(table)

    # TODO: Also show custom datasets from ~/.srl4c/datasets/
    console.print("\n[dim]CUSTOM (~/.srl4c/datasets/)[/dim]")
    console.print("  [dim](none)[/dim]\n")


def show_dataset(console: Console, name: str):
    """Show dataset details"""
    datasets = get_builtin_datasets()

    if name not in datasets:
        console.print(f"[red]Dataset not found: {name}[/red]")
        return

    info = datasets[name]
    df = pd.read_csv(info["path"])

    console.print(f"\n[bold cyan]Dataset:[/bold cyan] {name}")
    console.print(f"[dim]Path: {info['path']}[/dim]")
    console.print(f"Prompts: {info['prompts']}\n")

    if info["principles"]:
        console.print("[bold]Principles covered:[/bold]")
        # Count prompts per principle
        cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
        if cat_col:
            for principle in sorted(info["principles"]):
                count = len(df[df[cat_col] == principle])
                # Extract just the principle name
                short_name = principle.split(".")[-1] if "." in principle else principle
                console.print(f"  {short_name}: {count} prompts")

    console.print("\n[bold]Sample prompts:[/bold]")
    prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)
    if prompt_col:
        for i, row in df.head(5).iterrows():
            prompt = str(row[prompt_col])[:60]
            console.print(f"  {i+1}. \"{prompt}...\"")

    console.print()
