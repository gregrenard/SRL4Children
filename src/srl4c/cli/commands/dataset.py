"""Dataset commands - list and show datasets from database."""

from rich.console import Console
from rich.table import Table

from srl4c.core.datasets import list_datasets as core_list_datasets
from srl4c.db.models import init_db


def list_datasets(console: Console):
    """List available datasets (built-in and custom from database)."""
    init_db()
    datasets = core_list_datasets()

    if not datasets:
        console.print("[dim]No datasets found.[/dim]")
        console.print("[dim]Add custom datasets with: srl4c dataset add <file.csv> --name <name>[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Prompts", justify="right", no_wrap=True)
    table.add_column("Criteria", justify="right", no_wrap=True)
    table.add_column("Type", no_wrap=True)

    for ds in datasets:
        # Count unique criteria
        criteria_count = len(ds.criteria_breakdown) if ds.criteria_breakdown else 0
        ds_type = "[dim]built-in[/dim]" if ds.is_builtin else "custom"

        table.add_row(
            ds.name,
            str(ds.prompt_count),
            str(criteria_count),
            ds_type,
        )

    console.print("\n[bold]Available Datasets[/bold]")
    console.print(table)
    console.print()


def show_dataset(console: Console, name: str):
    """Show dataset details including criteria breakdown."""
    from srl4c.core.datasets import get_dataset, get_dataset_prompts

    init_db()
    dataset = get_dataset(name)

    if not dataset:
        console.print(f"[red]Dataset not found: {name}[/red]")
        available = [ds.name for ds in core_list_datasets()]
        if available:
            console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        return

    console.print(f"\n[bold cyan]Dataset:[/bold cyan] {name}")
    ds_type = "built-in" if dataset.is_builtin else "custom"
    console.print(f"[dim]Type: {ds_type}[/dim]")
    console.print(f"Total prompts: {dataset.prompt_count}\n")

    if dataset.criteria_breakdown:
        # Group by cue (top-level category)
        by_cue: dict[str, dict[str, int]] = {}
        for criteria_id, count in dataset.criteria_breakdown.items():
            parts = criteria_id.split(".")
            if len(parts) >= 2:
                # e.g., "emotional_reliance.interactional.flattery" -> cue is "interactional"
                cue = parts[1] if len(parts) > 1 else parts[0]
                by_cue.setdefault(cue, {})[criteria_id] = count

        console.print("[bold]Criteria breakdown:[/bold]")
        table = Table(show_edge=False, show_header=True)
        table.add_column("Criteria", style="dim")
        table.add_column("Prompts", justify="right")

        for cue in sorted(by_cue.keys()):
            # Cue header
            cue_total = sum(by_cue[cue].values())
            table.add_row(f"[bold]{cue}[/bold]", f"[bold]{cue_total}[/bold]")

            # Individual criteria
            for criteria_id in sorted(by_cue[cue].keys()):
                count = by_cue[cue][criteria_id]
                # Show just behavior name for readability
                short_name = criteria_id.split(".")[-1] if "." in criteria_id else criteria_id
                table.add_row(f"  {short_name}", str(count))

        console.print(table)

    # Show sample prompts
    if dataset.csv_content:
        console.print("\n[bold]Sample prompts:[/bold]")
        try:
            result = get_dataset_prompts(name, page=1, page_size=5)
            for p in result["prompts"]:
                prompt_text = p.get("prompt", "")
                criteria_id = p.get("criteria_id", "")
                short_prompt = prompt_text[:60] + "..." if len(prompt_text) > 60 else prompt_text
                behavior = criteria_id.split(".")[-1] if "." in criteria_id else criteria_id
                console.print(f"  - [dim]{behavior}:[/dim] \"{short_prompt}\"")
        except ValueError:
            pass

    console.print()
