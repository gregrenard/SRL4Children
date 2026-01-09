"""Attack commands implementation"""

import time
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from srl4c.db.models import Attack, Record
from srl4c.db.repository import (
    EndpointRepository, AttackRepository, RecordRepository, generate_id
)
from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter
from srl4c.cli.commands.dataset import get_builtin_datasets, DATA_DIR


def get_dataset_path(name: str) -> Path:
    """Get path to dataset by name"""
    datasets = get_builtin_datasets()
    if name in datasets:
        return datasets[name]["path"]
    # Check custom datasets
    custom_dir = Path.home() / ".srl4c" / "datasets"
    custom_path = custom_dir / f"{name}.csv"
    if custom_path.exists():
        return custom_path
    return None


def load_dataset(path: Path) -> pd.DataFrame:
    """Load dataset and normalize column names"""
    df = pd.read_csv(path)

    # Find columns
    prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)
    cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
    id_col = next((c for c in df.columns if c.lower() in ["promptid", "id", "uid"]), None)

    if not prompt_col:
        raise ValueError("Dataset must have a 'Prompt' or 'Question' column")

    # Normalize
    result = pd.DataFrame()
    result["prompt"] = df[prompt_col]
    result["principle_id"] = df[cat_col] if cat_col else ""
    result["id"] = df[id_col] if id_col else range(len(df))

    return result


def run_attack(console: Console, endpoint_name: str, dataset_name: str):
    """Run an attack against an endpoint"""
    # Get endpoint
    try:
        endpoint = EndpointRepository.get_by_id_or_name(endpoint_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not endpoint:
        console.print(f"[red]Endpoint not found: {endpoint_name}[/red]")
        return

    # Get dataset
    dataset_path = get_dataset_path(dataset_name)
    if not dataset_path:
        console.print(f"[red]Dataset not found: {dataset_name}[/red]")
        return

    try:
        df = load_dataset(dataset_path)
    except Exception as e:
        console.print(f"[red]Error loading dataset: {e}[/red]")
        return

    console.print(f"\nStarting attack...")
    console.print(f"  Endpoint: [cyan]{endpoint.name}[/cyan] ({endpoint.id})")
    console.print(f"  Dataset:  [cyan]{dataset_name}[/cyan] ({len(df)} prompts)\n")

    # Create attack record
    attack = Attack(
        id=generate_id(),
        endpoint_id=endpoint.id,
        dataset_name=dataset_name,
        status="running",
        total_prompts=len(df),
        completed_prompts=0,
    )
    AttackRepository.create(attack)
    console.print(f"Attack [cyan]{attack.id}[/cyan] created\n")

    # Create adapter
    if endpoint.type == "openai":
        adapter = OpenAIAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)
    else:
        adapter = SimpleAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)

    # Send prompts
    completed = 0
    errors = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Sending prompts...", total=len(df))

        for _, row in df.iterrows():
            prompt = str(row["prompt"])
            principle_id = str(row["principle_id"]) if row["principle_id"] else ""

            # Create record
            record = Record(
                id=generate_id(),
                attack_id=attack.id,
                prompt=prompt,
                principle_id=principle_id,
            )
            RecordRepository.create(record)

            # Send to endpoint
            try:
                response = adapter.send_message(prompt)
                RecordRepository.update_response(record.id, response=response)
                completed += 1
            except Exception as e:
                RecordRepository.update_response(record.id, error=str(e))
                errors += 1

            progress.update(task, advance=1)

            # Small delay to avoid rate limiting
            time.sleep(0.1)

    # Update attack status
    AttackRepository.update_status(attack.id, "completed", completed)
    EndpointRepository.update_last_used(endpoint.id)

    console.print(f"\n[green]✓[/green] Attack completed")
    console.print(f"  ID:        [cyan]{attack.id}[/cyan]")
    console.print(f"  Prompts:   {completed} sent, {errors} errors")
    console.print(f"\nNext step: [cyan]srl4c score run {attack.id} --age child --weights balanced[/cyan]\n")


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
        status_style = "green" if attack.status == "completed" else "yellow"
        prompts = f"{attack.completed_prompts}/{attack.total_prompts}"
        date = attack.started_at[:10] if attack.started_at else ""

        table.add_row(
            attack.id[:8],
            endpoint_name,
            attack.dataset_name,
            f"[{status_style}]{attack.status}[/{status_style}]",
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

    console.print(f"\n[bold]Attack:[/bold] {attack.id}")
    console.print(f"[bold]Status:[/bold] {attack.status}")
    console.print(f"[bold]Endpoint:[/bold] {endpoint_name} ({attack.endpoint_id})")
    console.print(f"[bold]Dataset:[/bold] {attack.dataset_name}")
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
            if record.principle_id:
                principle_short = record.principle_id.split(".")[-1]
                console.print(f"      [dim]Principle: {principle_short}[/dim]")
            console.print()
