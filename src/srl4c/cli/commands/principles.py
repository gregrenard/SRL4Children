"""Principles commands"""

from rich.console import Console
from rich.table import Table

from srl4c.core.datasets import get_prompt_stats_by_principle
from srl4c.criteria import get_criteria_loader


def list_principles(console: Console):
    """List all design principles with prompt counts"""
    loader = get_criteria_loader()
    registry = loader.load_registry()
    criteria = registry.get("criteria", {})
    stats = get_prompt_stats_by_principle()

    table = Table(title="Design Principles")
    table.add_column("Category", style="cyan")
    table.add_column("Subcategory", style="blue")
    table.add_column("Principle", style="green")
    table.add_column("Prompts", justify="right", style="yellow")
    table.add_column("Version", style="dim")

    total_prompts = 0
    for criterion_id, info in sorted(criteria.items()):
        # Match to stats (handle version suffix)
        base_id = criterion_id.rsplit("__", 1)[0] if "__" in criterion_id else criterion_id
        prompt_count = stats.get(criterion_id, stats.get(base_id, {})).get("count", 0)
        total_prompts += prompt_count

        table.add_row(
            info["category"],
            info["subcategory"],
            info["name"],
            str(prompt_count) if prompt_count > 0 else "—",
            info["version"],
        )

    console.print(table)
    console.print(f"\n[dim]{len(criteria)} principles, {total_prompts} total prompts[/dim]")


def show_principle(console: Console, principle_id: str):
    """Show principle details"""
    loader = get_criteria_loader()
    registry = loader.load_registry()
    criteria = registry.get("criteria", {})

    # Find matching principle (by name or full ID)
    match = None
    for cid, info in criteria.items():
        if info["name"] == principle_id or cid == principle_id or cid.startswith(principle_id):
            match = (cid, info)
            break

    if not match:
        console.print(f"[red]Principle not found: {principle_id}[/red]")
        return

    cid, info = match

    # Load full criterion with prompt content
    config = loader.load_criterion(cid)

    console.print(f"\n[bold cyan]Principle:[/bold cyan] {info['category']}.{info['subcategory']}.{info['name']}")
    console.print(f"[dim]Version: {info['version']} | Author: {info['author']}[/dim]\n")

    console.print(f"[bold]Description:[/bold]\n  {info['description']}\n")

    if config.prompt_content:
        if "scoring_guide" in config.prompt_content:
            console.print("[bold]Scoring Guide:[/bold]")
            for line in config.prompt_content["scoring_guide"].strip().split("\n"):
                console.print(f"  {line}")
            console.print()

        if "examples" in config.prompt_content:
            console.print("[bold]Examples:[/bold]")
            console.print(f"[dim]{config.prompt_content['examples'][:500]}...[/dim]")

    console.print(f"\n[dim]Tags: {', '.join(info.get('tags', []))}[/dim]")
