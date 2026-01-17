"""Endpoint commands implementation"""

from rich.console import Console
from rich.table import Table

from srl4c.core.endpoints import send_prompt
from srl4c.db.models import Endpoint
from srl4c.db.repository import EndpointRepository, generate_id


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


def test_endpoint(console: Console, id_or_name: str, prompt: str = None):
    """Test endpoint connectivity with optional custom prompt"""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(id_or_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not endpoint:
        console.print(f"[red]Endpoint not found: {id_or_name}[/red]")
        return

    # Use custom prompt or default
    test_prompt = prompt or "Hello!"

    console.print(f"Testing '[cyan]{endpoint.name}[/cyan]' ({endpoint.id})...")
    console.print(f'  → Sending: "{test_prompt[:50]}{"..." if len(test_prompt) > 50 else ""}"')

    result = send_prompt(id_or_name, test_prompt)

    if result["success"]:
        response_preview = result["response"][:100] if result["response"] else ""
        console.print(f'  ← Response: "{response_preview}{"..." if len(result["response"] or "") > 100 else ""}"')
        console.print(f"  [green]✓[/green] Endpoint is healthy (latency: {result['latency_ms']}ms)")
    else:
        console.print(f"  [red]✗[/red] Connection failed: {result['error']}")


def remove_endpoint(console: Console, id_or_name: str, force: bool = False, yes: bool = False):
    """Remove an endpoint"""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(id_or_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if not endpoint:
        console.print(f"[red]Endpoint not found: {id_or_name}[/red]")
        return

    # Get preview of what will be deleted
    preview = EndpointRepository.delete_preview(endpoint.id)
    has_children = preview.get("has_children", False)

    # Show confirmation
    console.print(f"\n[bold]Delete Endpoint:[/bold] [cyan]{endpoint.name}[/cyan] ({endpoint.id[:8]})")

    if has_children:
        will_delete = preview.get("will_delete", {})
        console.print("\n[yellow]⚠ Warning: This endpoint has related data that will also be deleted:[/yellow]")
        if will_delete.get("attacks"):
            console.print(f"  • {will_delete['attacks']} attack(s)")
        if will_delete.get("records"):
            console.print(f"  • {will_delete['records']} record(s)")
        if will_delete.get("scores"):
            console.print(f"  • {will_delete['scores']} score(s)")
        if will_delete.get("evaluations"):
            console.print(f"  • {will_delete['evaluations']} evaluation(s)")
        if will_delete.get("guardrail_sets"):
            console.print(f"  • {will_delete['guardrail_sets']} guardrail set(s)")
        if will_delete.get("guardrails"):
            console.print(f"  • {will_delete['guardrails']} guardrail rule(s)")

        if not force:
            console.print("\n[dim]Use --force to delete with all related data.[/dim]")
            return

    # Confirm unless --yes
    if not yes:
        confirm_text = "Delete ALL related data" if has_children else "Delete"
        from rich.prompt import Confirm

        if not Confirm.ask(f"\n{confirm_text}?"):
            console.print("[dim]Cancelled[/dim]")
            return

    deleted = EndpointRepository.delete(endpoint.id, cascade=force or has_children)
    console.print(f"\n[green]✓[/green] Removed endpoint '[cyan]{endpoint.name}[/cyan]'")

    if deleted and any(deleted.values()):
        parts = []
        if deleted.get("attacks"):
            parts.append(f"{deleted['attacks']} attacks")
        if deleted.get("records"):
            parts.append(f"{deleted['records']} records")
        if deleted.get("scores"):
            parts.append(f"{deleted['scores']} scores")
        if deleted.get("evaluations"):
            parts.append(f"{deleted['evaluations']} evaluations")
        if deleted.get("guardrail_sets"):
            parts.append(f"{deleted['guardrail_sets']} guardrail sets")
        if deleted.get("guardrails"):
            parts.append(f"{deleted['guardrails']} guardrails")
        if parts:
            console.print(f"  Deleted: {', '.join(parts)}")
