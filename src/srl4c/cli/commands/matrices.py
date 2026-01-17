"""Matrix commands - manage scoring matrices"""

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from srl4c.core import matrices as core_matrices


def list_matrices(console: Console):
    """List all scoring matrices"""
    matrices = core_matrices.list_matrices()

    if not matrices:
        console.print("[dim]No scoring matrices found.[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description")
    table.add_column("Built-in", no_wrap=True)
    table.add_column("Created", style="dim", no_wrap=True)

    for m in matrices:
        builtin = "[green]✓[/green]" if m.is_builtin else ""
        created = str(m.created_at)[:10] if m.created_at else ""
        table.add_row(
            m.name,
            m.description or "-",
            builtin,
            created,
        )

    console.print(table)


def show_matrix(console: Console, name: str):
    """Show matrix details with entries"""
    matrix = core_matrices.get_matrix(name)

    if not matrix:
        console.print(f"[red]Matrix not found: {name}[/red]")
        return

    console.print(f"\n[bold]Matrix:[/bold] {matrix.name}")
    console.print(f"[bold]Description:[/bold] {matrix.description or 'N/A'}")
    console.print(f"[bold]Built-in:[/bold] {'Yes' if matrix.is_builtin else 'No'}")

    entries = core_matrices.get_matrix_entries(matrix.id)
    if entries:
        console.print(f"\n[bold]Entries ({len(entries)}):[/bold]")

        table = Table(show_edge=False)
        table.add_column("Behavior", style="cyan")
        table.add_column("Age", no_wrap=True)
        table.add_column("Presence", justify="right", no_wrap=True)
        table.add_column("→ Score", justify="right", no_wrap=True)

        for e in entries[:20]:  # Show first 20
            short_behavior = e.behavior_id.split(".")[-1] if "." in e.behavior_id else e.behavior_id
            table.add_row(
                short_behavior,
                e.age_group,
                str(e.presence_level),
                f"{e.score:.1f}",
            )

        console.print(table)
        if len(entries) > 20:
            console.print(f"[dim]... and {len(entries) - 20} more entries[/dim]")
    else:
        console.print("\n[dim]No entries (uses identity mapping: presence → score)[/dim]")


def create_matrix(console: Console, name: str, description: str = None):
    """Create a new scoring matrix"""
    try:
        matrix = core_matrices.create_matrix(name=name, description=description)
        console.print(f"[green]✓[/green] Created matrix: [cyan]{matrix.name}[/cyan]")
        console.print(f"  ID: {matrix.id}")
        console.print(f"\n[dim]Add entries with: srl4c matrices clone {name} --from <source>[/dim]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


def clone_matrix(console: Console, source: str, new_name: str, description: str = None):
    """Clone an existing matrix"""
    try:
        matrix = core_matrices.clone_matrix(
            source_name_or_id=source,
            new_name=new_name,
            description=description,
        )
        entries = core_matrices.get_matrix_entries(matrix.id)
        console.print(f"[green]✓[/green] Cloned [cyan]{source}[/cyan] → [cyan]{matrix.name}[/cyan]")
        console.print(f"  ID: {matrix.id}")
        console.print(f"  Entries: {len(entries)}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


def delete_matrix(console: Console, name: str, yes: bool = False):
    """Delete a scoring matrix"""
    matrix = core_matrices.get_matrix(name)
    if not matrix:
        console.print(f"[red]Matrix not found: {name}[/red]")
        return

    if matrix.is_builtin:
        console.print(f"[red]Cannot delete built-in matrix: {name}[/red]")
        return

    entries = core_matrices.get_matrix_entries(matrix.id)
    console.print(f"\n[bold]Delete Matrix:[/bold] [cyan]{matrix.name}[/cyan]")
    console.print(f"  Entries: {len(entries)}")

    if not yes:
        if not Confirm.ask("\nDelete this matrix?"):
            console.print("[dim]Cancelled[/dim]")
            return

    try:
        core_matrices.delete_matrix(name)
        console.print(f"[green]✓[/green] Deleted matrix: {name}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
