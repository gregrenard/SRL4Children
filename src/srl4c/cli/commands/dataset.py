"""Dataset commands - list and show datasets discovered from filesystem."""

from rich.console import Console
from rich.table import Table

from srl4c.registry import get_registry_loader


def list_datasets(console: Console):
    """List available datasets (auto-discovered from data/datasets/)."""
    loader = get_registry_loader()
    datasets = loader.list_datasets()

    if not datasets:
        console.print("[dim]No datasets found in data/datasets/[/dim]")
        console.print("[dim]Add CSV files with columns: PromptID, Category, Prompt[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Prompts", justify="right", no_wrap=True)
    table.add_column("Criteria", justify="right", no_wrap=True)
    table.add_column("Categories", no_wrap=True)

    for ds in datasets:
        # Get unique categories from criteria breakdown
        categories = set()
        for criteria_id in ds.criteria_breakdown.keys():
            if "." in criteria_id:
                categories.add(criteria_id.split(".")[0])

        categories_str = ", ".join(sorted(categories)) if categories else "—"
        table.add_row(
            ds.name,
            str(ds.prompt_count),
            str(len(ds.criteria_breakdown)),
            categories_str,
        )

    console.print("\n[bold]Available Datasets[/bold]")
    console.print(table)
    console.print()


def show_dataset(console: Console, name: str):
    """Show dataset details including criteria breakdown."""
    loader = get_registry_loader()

    try:
        dataset = loader.get_dataset(name)
    except ValueError:
        console.print(f"[red]Dataset not found: {name}[/red]")
        available = [ds.name for ds in loader.list_datasets()]
        if available:
            console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        return

    console.print(f"\n[bold cyan]Dataset:[/bold cyan] {name}")
    console.print(f"[dim]File: {dataset.file}[/dim]")
    console.print(f"Total prompts: {dataset.prompt_count}\n")

    if dataset.criteria_breakdown:
        # Group by category
        by_category: dict[str, dict[str, int]] = {}
        for criteria_id, count in dataset.criteria_breakdown.items():
            parts = criteria_id.split(".")
            if len(parts) >= 1:
                category = parts[0]
                by_category.setdefault(category, {})[criteria_id] = count

        console.print("[bold]Criteria breakdown:[/bold]")
        table = Table(show_edge=False, show_header=True)
        table.add_column("Criteria", style="dim")
        table.add_column("Prompts", justify="right")

        for category in sorted(by_category.keys()):
            # Category header
            category_total = sum(by_category[category].values())
            table.add_row(f"[bold]{category}[/bold]", f"[bold]{category_total}[/bold]")

            # Individual criteria
            for criteria_id in sorted(by_category[category].keys()):
                count = by_category[category][criteria_id]
                # Show just subcategory.name for readability
                short_name = ".".join(criteria_id.split(".")[1:]) if "." in criteria_id else criteria_id
                table.add_row(f"  {short_name}", str(count))

        console.print(table)

    # Show sample prompts
    console.print("\n[bold]Sample prompts:[/bold]")
    prompts = loader.load_dataset_prompts(name)
    for p in prompts[:5]:
        short_prompt = p.prompt[:60] + "..." if len(p.prompt) > 60 else p.prompt
        console.print(f"  • [dim]{p.criteria_id.split('.')[-1]}:[/dim] \"{short_prompt}\"")

    console.print()
