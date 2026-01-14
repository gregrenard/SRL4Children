"""Criteria commands - list and show criteria definitions."""

from rich.console import Console
from rich.table import Table

from srl4c.registry import get_registry_loader


def list_criteria(console: Console):
    """List all criteria definitions."""
    loader = get_registry_loader()
    criteria = loader.list_criteria()

    if not criteria:
        console.print("[dim]No criteria found in registry[/dim]")
        return

    # Group by category
    by_category: dict[str, list] = {}
    for c in criteria:
        by_category.setdefault(c.category, []).append(c)

    console.print("\n[bold]Criteria (What can be tested)[/bold]\n")

    for category in sorted(by_category.keys()):
        console.print(f"[bold cyan]{category.upper()}[/bold cyan]")

        table = Table(show_edge=False, show_header=False, padding=(0, 2))
        table.add_column("ID", style="dim")
        table.add_column("Description")

        for c in sorted(by_category[category], key=lambda x: x.id):
            # Show subcategory.name
            short_id = f"{c.subcategory}.{c.name}"
            table.add_row(short_id, c.description[:60] + "..." if len(c.description) > 60 else c.description)

        console.print(table)
        console.print()


def show_criteria(console: Console, criteria_id: str):
    """Show criteria details."""
    loader = get_registry_loader()

    # Try to resolve partial ID
    if "." not in criteria_id or criteria_id.count(".") < 2:
        # Try to find matching criteria
        matches = loader.resolve_criteria_selection(criteria_id)
        if len(matches) == 0:
            console.print(f"[red]Criteria not found: {criteria_id}[/red]")
            return
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple criteria match '{criteria_id}':[/yellow]")
            for m in matches:
                console.print(f"  • {m}")
            return
        criteria_id = matches[0]

    try:
        criteria = loader.get_criteria(criteria_id)
    except ValueError:
        console.print(f"[red]Criteria not found: {criteria_id}[/red]")
        return

    console.print(f"\n[bold cyan]Criteria:[/bold cyan] {criteria.id}")
    console.print(f"[dim]Category: {criteria.category} > {criteria.subcategory}[/dim]\n")
    console.print(f"[bold]Description:[/bold] {criteria.description}")

    if criteria.tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(criteria.tags)}")

    # Show which judges implement this criteria
    console.print("\n[bold]Judge implementations:[/bold]")
    for judge_name in loader.list_judges():
        judge = loader.get_judge(judge_name)
        if criteria_id in judge.implementations:
            impl = judge.implementations[criteria_id]
            inherited = " [dim](inherited)[/dim]" if judge.inherits_from else ""
            console.print(f"  • {judge_name}: v{impl.version}{inherited}")

    console.print()


def list_judges_registry(console: Console):
    """List evaluation judges (policies) from registry."""
    loader = get_registry_loader()
    judge_names = loader.list_judges()

    if not judge_names:
        console.print("[dim]No judges found in registry[/dim]")
        return

    console.print("\n[bold]Evaluation Judges (How to evaluate)[/bold]\n")

    table = Table(show_edge=False)
    table.add_column("Name", style="cyan")
    table.add_column("Inherits", style="dim")
    table.add_column("Description")

    for name in judge_names:
        judge = loader.get_judge(name)
        inherits = judge.inherits_from or "—"
        table.add_row(name, inherits, judge.description)

    console.print(table)
    console.print()


def show_judge_registry(console: Console, judge_name: str):
    """Show evaluation judge details from registry."""
    loader = get_registry_loader()

    try:
        judge = loader.get_judge(judge_name)
    except ValueError:
        console.print(f"[red]Judge not found: {judge_name}[/red]")
        available = loader.list_judges()
        if available:
            console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        return

    console.print(f"\n[bold cyan]Judge:[/bold cyan] {judge.name}")
    if judge.inherits_from:
        console.print(f"[dim]Inherits from: {judge.inherits_from}[/dim]")
    console.print(f"\n{judge.description}\n")

    # Show weight overrides
    if judge.weights.get("categories"):
        console.print("[bold]Category weights:[/bold]")
        table = Table(show_edge=False, show_header=False)
        table.add_column("Category")
        table.add_column("Weight", justify="right")

        for cat, weight in sorted(judge.weights["categories"].items()):
            table.add_row(cat, f"{weight:.2f}")

        console.print(table)
        console.print()

    # Show implementation count
    impl_count = len(judge.implementations)
    console.print(f"[bold]Implementations:[/bold] {impl_count} criteria")

    # If this judge has overrides (not default), show them
    if judge.inherits_from:
        # Find which implementations are overridden
        parent = loader.get_judge(judge.inherits_from)
        overrides = []
        for cid, impl in judge.implementations.items():
            parent_impl = parent.implementations.get(cid)
            if parent_impl and impl.file != parent_impl.file:
                overrides.append(cid)

        if overrides:
            console.print(f"\n[bold]Overridden criteria:[/bold]")
            for cid in overrides:
                console.print(f"  • {cid}")

    console.print()
