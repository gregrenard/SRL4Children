"""Attack commands implementation"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from srl4c.db.repository import EndpointRepository, AttackRepository, RecordRepository, DatasetRepository


def _get_dataset_name(dataset_id: str) -> str:
    """Get dataset name from ID, with fallback."""
    if not dataset_id:
        return "unknown"
    dataset = DatasetRepository.get_by_id(dataset_id)
    return dataset.name if dataset else dataset_id[:8]


def run_attack(console: Console, endpoint_name: str, dataset_name: str):
    """Run an attack against an endpoint"""
    from srl4c.core.attack import create_attack, run_attack as execute_attack

    # Create attack job (shared with API)
    try:
        attack_id = create_attack(endpoint_name, dataset_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Get attack details for display
    attack = AttackRepository.get_by_id(attack_id)
    endpoint = EndpointRepository.get_by_id(attack.endpoint_id)

    dataset_name_display = _get_dataset_name(attack.dataset_id)
    console.print(f"\nStarting attack...")
    console.print(f"  Endpoint: [cyan]{endpoint.name}[/cyan] ({endpoint.id})")
    console.print(f"  Dataset:  [cyan]{dataset_name_display}[/cyan] ({attack.total_prompts} prompts)\n")
    console.print(f"Attack [cyan]{attack_id}[/cyan] created\n")

    # Run with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Sending prompts...", total=attack.total_prompts)

        def on_progress(current: int, total: int):
            progress.update(task, completed=current, total=total)

        try:
            execute_attack(attack_id, on_progress=on_progress)
        except Exception as e:
            console.print(f"\n[red]✗[/red] Attack failed: {e}")
            return

    # Show result
    attack = AttackRepository.get_by_id(attack_id)
    records = RecordRepository.get_by_attack(attack_id)
    errors = sum(1 for r in records if r.error)

    console.print(f"\n[green]✓[/green] Attack completed")
    console.print(f"  ID:        [cyan]{attack.id}[/cyan]")
    console.print(f"  Prompts:   {attack.completed_prompts} sent, {errors} errors")
    console.print(f"\nNext step: [cyan]srl4c score run {attack.id} --age child --judge <JUDGE>[/cyan]")
    console.print(f"  (see available judges: [cyan]srl4c eval-judges list[/cyan])\n")


def list_attacks(console: Console):
    """List all attacks"""
    from rich.table import Table

    attacks = AttackRepository.list_all()

    if not attacks:
        console.print("[dim]No attacks yet. Use 'srl4c attack run' to start one.[/dim]")
        return

    # Get endpoint names
    endpoints = {ep.id: ep.name for ep in EndpointRepository.list_all()}

    table = Table(show_edge=False)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Endpoint", style="cyan", no_wrap=True)
    table.add_column("Dataset", style="blue", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Prompts", justify="right", no_wrap=True)
    table.add_column("Date", style="dim", no_wrap=True)

    for attack in attacks:
        endpoint_name = endpoints.get(attack.endpoint_id, attack.endpoint_id[:8])

        # Status styling
        status = attack.status
        if status == "completed":
            status_style = "green"
        elif status == "failed":
            status_style = "red"
        elif status == "running":
            status_style = "yellow"
        else:
            status_style = "dim"

        prompts = f"{attack.completed_prompts}/{attack.total_prompts}"
        date = attack.started_at[:10] if attack.started_at else ""
        dataset_name_display = _get_dataset_name(attack.dataset_id)

        table.add_row(
            attack.id[:8],
            endpoint_name,
            dataset_name_display,
            f"[{status_style}]{status}[/{status_style}]",
            prompts,
            date,
        )

    console.print(table)


def show_attack(console: Console, attack_id: str):
    """Show attack details"""
    try:
        attack = AttackRepository.get_by_id(attack_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not attack:
        console.print(f"[red]Attack not found: {attack_id}[/red]")
        return

    endpoint = EndpointRepository.get_by_id(attack.endpoint_id)
    endpoint_name = endpoint.name if endpoint else attack.endpoint_id

    dataset_name_display = _get_dataset_name(attack.dataset_id)

    console.print(f"\n[bold]Attack:[/bold] {attack.id}")
    console.print(f"[bold]Status:[/bold] {attack.status}")
    if attack.error_message:
        console.print(f"[bold]Error:[/bold] [red]{attack.error_message}[/red]")
    console.print(f"[bold]Endpoint:[/bold] {endpoint_name} ({attack.endpoint_id})")
    console.print(f"[bold]Dataset:[/bold] {dataset_name_display}")
    console.print(f"[bold]Started:[/bold] {attack.started_at}")
    console.print(f"[bold]Completed:[/bold] {attack.completed_at or 'N/A'}")
    console.print(f"[bold]Records:[/bold] {attack.completed_prompts}/{attack.total_prompts}\n")

    # Show sample records
    records = RecordRepository.get_by_attack(attack.id)
    if records:
        console.print("[bold]Sample records:[/bold]")
        for i, record in enumerate(records[:5], 1):
            prompt_short = record.prompt[:50] + "..." if len(record.prompt) > 50 else record.prompt
            response_short = ""
            if record.response:
                response_short = record.response[:50] + "..." if len(record.response) > 50 else record.response
            elif record.error:
                response_short = f"[red]Error: {record.error[:30]}[/red]"

            console.print(f"  #{i} [cyan]Prompt:[/cyan] \"{prompt_short}\"")
            console.print(f"      [green]Response:[/green] \"{response_short}\"")
            if record.criteria_id:
                principle_short = record.criteria_id.split(".")[-1]
                console.print(f"      [dim]Principle: {principle_short}[/dim]")
            console.print()
