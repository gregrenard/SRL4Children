"""Endpoint commands implementation"""

from rich.console import Console
from rich.table import Table

from srl4c.db.models import Endpoint
from srl4c.db.repository import EndpointRepository, generate_id
from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter


def add_endpoint(
    console: Console,
    type: str,
    name: str,
    base_url: str = None,
    url: str = None,
    api_key_env: str = None,
    request_field: str = "message",
    response_field: str = "response",
):
    """Add a new endpoint"""
    # Validate
    if type == "openai" and not base_url:
        console.print("[red]Error: --base-url is required for openai type[/red]")
        return
    if type == "simple" and not url:
        console.print("[red]Error: --url is required for simple type[/red]")
        return

    # Check name doesn't exist
    existing = EndpointRepository.get_by_name(name)
    if existing:
        console.print(f"[red]Error: Endpoint '{name}' already exists[/red]")
        return

    # Build config
    config = {}
    if type == "simple":
        config["request_field"] = request_field
        config["response_field"] = response_field

    # Create endpoint
    endpoint = Endpoint(
        id=generate_id(),
        name=name,
        type=type,
        base_url=base_url or url,
        api_key_env=api_key_env,
        config=config,
    )

    EndpointRepository.create(endpoint)
    console.print(f"[green]✓[/green] Endpoint '[cyan]{name}[/cyan]' created (ID: {endpoint.id})")


def list_endpoints(console: Console):
    """List all endpoints"""
    endpoints = EndpointRepository.list_all()

    if not endpoints:
        console.print("[dim]No endpoints configured. Use 'srl4c endpoint add' to add one.[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="blue", no_wrap=True)
    table.add_column("URL", no_wrap=True)
    table.add_column("Last Used", style="dim", no_wrap=True)

    for ep in endpoints:
        last_used = ep.last_used_at[:10] if ep.last_used_at else "never"
        table.add_row(ep.id[:8], ep.name, ep.type, ep.base_url, last_used)

    console.print(table)


def test_endpoint(console: Console, id_or_name: str):
    """Test endpoint connectivity"""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(id_or_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not endpoint:
        console.print(f"[red]Endpoint not found: {id_or_name}[/red]")
        return

    console.print(f"Testing '[cyan]{endpoint.name}[/cyan]' ({endpoint.id})...")

    # Create adapter
    if endpoint.type == "openai":
        adapter = OpenAIAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)
    else:
        adapter = SimpleAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)

    # Test
    console.print(f"  → Sending: \"Hello, this is a test.\"")
    success, response, latency = adapter.test_connection()

    if success:
        console.print(f"  ← Response: \"{response}...\"")
        console.print(f"  [green]✓[/green] Endpoint is healthy (latency: {latency}ms)")
        EndpointRepository.update_last_used(endpoint.id)
    else:
        console.print(f"  [red]✗[/red] Connection failed: {response}")


def remove_endpoint(console: Console, id_or_name: str):
    """Remove an endpoint"""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(id_or_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not endpoint:
        console.print(f"[red]Endpoint not found: {id_or_name}[/red]")
        return

    EndpointRepository.delete(endpoint.id)
    console.print(f"[green]✓[/green] Removed endpoint '[cyan]{endpoint.name}[/cyan]'")
