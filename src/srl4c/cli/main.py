"""SRL4C CLI - Main entry point"""

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="srl4c",
    help="Safety Readiness Level for Children - Test your AI for child safety",
    no_args_is_help=True,
)
console = Console()

# Sub-command groups
endpoint_app = typer.Typer(help="Manage endpoints (AI apps to test)")
dataset_app = typer.Typer(help="Manage attack datasets")
attack_app = typer.Typer(help="Run attacks against endpoints")
score_app = typer.Typer(help="Score attack results")
guardrails_app = typer.Typer(help="Generate and manage guardrails")
principles_app = typer.Typer(help="View and manage design principles")
judges_app = typer.Typer(help="Manage judge configurations")
generators_app = typer.Typer(help="Manage guardrail generator configurations")
config_app = typer.Typer(help="Manage configuration")

app.add_typer(endpoint_app, name="endpoint")
app.add_typer(dataset_app, name="dataset")
app.add_typer(attack_app, name="attack")
app.add_typer(score_app, name="score")
app.add_typer(guardrails_app, name="guardrails")
app.add_typer(principles_app, name="principles")
app.add_typer(judges_app, name="judges")
app.add_typer(generators_app, name="generators")
app.add_typer(config_app, name="config")


# === INIT ===


@app.command()
def init():
    """Initialize SRL4C - create ~/.srl4c/ directory structure"""
    from srl4c.cli.commands.init import run_init

    run_init(console)


# === PIPELINE ===


@app.command(name="run-pipeline")
def pipeline_run(
    name: str = typer.Argument(..., help="Friendly name for the endpoint"),
    endpoint_type: str = typer.Option("simple", "--type", "-t", help="Endpoint type: 'openai' or 'simple'"),
    endpoint_url: str = typer.Option(
        ..., "--url", "-u", help="Endpoint URL (base URL for openai, full URL for simple)"
    ),
    api_key_env: str = typer.Option(None, "--api-key-env", "-k", help="Env var with API key"),
    base_url: str = typer.Option(None, "--base-url", help="Base URL (for openai type)"),
    dataset: str = typer.Option("anthropomorphism_question_mini", "--dataset", "-d", help="Dataset to use for attack"),
    age: str = typer.Option("child", "--age", "-a", help="Age context: child, teen, young_adult"),
    weights: str = typer.Option("balanced", "--weights", "-w", help="Weight preset"),
    request_field: str = typer.Option("message", "--request-field", help="Request field (simple type)"),
    response_field: str = typer.Option("response", "--response-field", help="Response field (simple type)"),
    max_rules: int = typer.Option(3, "--max-rules", help="Max guardrails per criterion"),
    max_total: int = typer.Option(20, "--max-total", help="Max total guardrails"),
    deploy_worker: bool = typer.Option(False, "--deploy-worker", help="Deploy Cloudflare Worker"),
):
    """Run the full SRL4C pipeline in one command.

    Creates endpoint → runs attack → scores results → generates guardrails.
    """
    from srl4c.cli.commands.pipeline import run_pipeline

    run_pipeline(
        console,
        name,
        endpoint_type,
        endpoint_url,
        api_key_env=api_key_env,
        dataset=dataset,
        age=age,
        weights=weights,
        request_field=request_field,
        response_field=response_field,
        base_url=base_url,
        max_rules=max_rules,
        max_total=max_total,
        deploy_worker=deploy_worker,
    )


# === ENDPOINT ===


@endpoint_app.command("add")
def endpoint_add(
    type: str = typer.Argument(..., help="Endpoint type: 'openai' or 'simple'"),
    name: str = typer.Option(..., "--name", "-n", help="Friendly name for this endpoint"),
    base_url: str = typer.Option(None, "--base-url", "-u", help="Base URL (for openai type)"),
    url: str = typer.Option(None, "--url", help="Full URL (for simple type)"),
    api_key_env: str = typer.Option(None, "--api-key-env", "-k", help="Env var name containing API key"),
    request_field: str = typer.Option("message", "--request-field", help="JSON field for request (simple type)"),
    response_field: str = typer.Option("response", "--response-field", help="JSON field for response (simple type)"),
):
    """Add a new endpoint to test"""
    from srl4c.cli.commands.endpoint import add_endpoint

    add_endpoint(console, type, name, base_url, url, api_key_env, request_field, response_field)


@endpoint_app.command("list")
def endpoint_list():
    """List configured endpoints"""
    from srl4c.cli.commands.endpoint import list_endpoints

    list_endpoints(console)


@endpoint_app.command("test")
def endpoint_test(id: str = typer.Argument(..., help="Endpoint ID or name")):
    """Test endpoint connectivity"""
    from srl4c.cli.commands.endpoint import test_endpoint

    test_endpoint(console, id)


@endpoint_app.command("remove")
def endpoint_remove(
    id: str = typer.Argument(..., help="Endpoint ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete with all related attacks/scores"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Remove an endpoint"""
    from srl4c.cli.commands.endpoint import remove_endpoint

    remove_endpoint(console, id, force=force, yes=yes)


# === DATASET ===


@dataset_app.command("list")
def dataset_list():
    """List available datasets (built-in and custom)"""
    from srl4c.cli.commands.dataset import list_datasets

    list_datasets(console)


@dataset_app.command("show")
def dataset_show(name: str = typer.Argument(..., help="Dataset name")):
    """Show dataset details"""
    from srl4c.cli.commands.dataset import show_dataset

    show_dataset(console, name)


@dataset_app.command("validate")
def dataset_validate(file: Path = typer.Argument(..., help="Path to CSV file")):
    """Validate a dataset CSV file"""
    console.print(f"[yellow]TODO:[/yellow] Validate dataset '{file}'")


@dataset_app.command("add")
def dataset_add(
    file: Path = typer.Argument(..., help="Path to CSV file"),
    name: str = typer.Option(..., "--name", "-n", help="Name for the dataset"),
):
    """Add a custom dataset"""
    console.print(f"[yellow]TODO:[/yellow] Add dataset '{file}' as '{name}'")


# === ATTACK ===


@attack_app.command("run")
def attack_run(
    endpoint: str = typer.Option(..., "--endpoint", "-e", help="Endpoint name or ID"),
    dataset: str = typer.Option(..., "--dataset", "-d", help="Dataset name"),
):
    """Run an attack against an endpoint"""
    from srl4c.cli.commands.attack import run_attack

    run_attack(console, endpoint, dataset)


@attack_app.command("list")
def attack_list():
    """List attacks"""
    from srl4c.cli.commands.attack import list_attacks

    list_attacks(console)


@attack_app.command("show")
def attack_show(id: str = typer.Argument(..., help="Attack ID")):
    """Show attack details"""
    from srl4c.cli.commands.attack import show_attack

    show_attack(console, id)


@attack_app.command("delete")
def attack_delete(
    id: str = typer.Argument(..., help="Attack ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete an attack and all its records/scores"""
    from rich.prompt import Confirm

    from srl4c.db.repository import AttackRepository

    try:
        preview = AttackRepository.delete_preview(id)
        if preview is None:
            console.print(f"[red]Attack not found: {id}[/red]")
            return

        attack = preview.get("attack", {})
        has_children = preview.get("has_children", False)
        will_delete = preview.get("will_delete", {})

        console.print(f"\n[bold]Delete Attack:[/bold] [cyan]{attack.get('id', id)[:8]}[/cyan]")
        console.print(f"  Dataset: {attack.get('dataset_name', 'unknown')}")

        if has_children:
            console.print("\n[yellow]⚠ This will also delete:[/yellow]")
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

        if not yes:
            confirm_text = "Delete ALL related data" if has_children else "Delete"
            if not Confirm.ask(f"\n{confirm_text}?"):
                console.print("[dim]Cancelled[/dim]")
                return

        deleted = AttackRepository.delete(id, cascade=True)
        console.print(f"\n[green]✓[/green] Deleted attack [cyan]{id[:8]}[/cyan]")

        if deleted and any(deleted.values()):
            parts = []
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

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


# === SCORE ===


@score_app.command("run")
def score_run(
    attack: str = typer.Argument(..., help="Attack ID"),
    age: str = typer.Option("child", "--age", "-a", help="Age context: child, teen, young_adult, emerging"),
    weights: str = typer.Option("balanced", "--weights", "-w", help="Weight preset (see ~/.srl4c/weights.yaml)"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, markdown"),
    threshold: float = typer.Option(None, "--threshold", "-t", help="Fail if score below threshold"),
):
    """Score an attack's results"""
    from srl4c.cli.commands.score import run_score

    run_score(console, attack, age, weights, format, threshold)


@score_app.command("list")
def score_list():
    """List score runs"""
    from srl4c.cli.commands.score import list_scores

    list_scores(console)


@score_app.command("show")
def score_show(id: str = typer.Argument(..., help="Score ID")):
    """Show score details"""
    from srl4c.cli.commands.score import show_score

    show_score(console, id)


@score_app.command("failures")
def score_failures(id: str = typer.Argument(..., help="Score ID")):
    """Show failures from a score run"""
    from srl4c.cli.commands.score import show_failures

    show_failures(console, id)


@score_app.command("report")
def score_report(
    id: str = typer.Argument(..., help="Score ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
):
    """Generate detailed Markdown report"""
    from srl4c.cli.commands.score import generate_report

    generate_report(console, id, output)


@score_app.command("delete")
def score_delete(
    id: str = typer.Argument(..., help="Score ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a score and its evaluations"""
    from rich.prompt import Confirm

    from srl4c.db.repository import ScoreRepository

    try:
        preview = ScoreRepository.delete_preview(id)
        if preview is None:
            console.print(f"[red]Score not found: {id}[/red]")
            return

        score = preview.get("score", {})
        has_children = preview.get("has_children", False)
        will_delete = preview.get("will_delete", {})

        console.print(f"\n[bold]Delete Score:[/bold] [cyan]{score.get('id', id)[:8]}[/cyan]")
        console.print(f"  Age: {score.get('age_context', 'unknown')}")
        if score.get("final_score"):
            console.print(f"  Final score: {score['final_score']:.1f}/5.0")

        if has_children:
            console.print("\n[yellow]⚠ This will also delete:[/yellow]")
            if will_delete.get("evaluations"):
                console.print(f"  • {will_delete['evaluations']} evaluation(s)")
            if will_delete.get("guardrail_sets"):
                console.print(f"  • {will_delete['guardrail_sets']} guardrail set(s)")
            if will_delete.get("guardrails"):
                console.print(f"  • {will_delete['guardrails']} guardrail rule(s)")

        if not yes:
            confirm_text = "Delete ALL related data" if has_children else "Delete"
            if not Confirm.ask(f"\n{confirm_text}?"):
                console.print("[dim]Cancelled[/dim]")
                return

        deleted = ScoreRepository.delete(id)
        console.print(f"\n[green]✓[/green] Deleted score [cyan]{id[:8]}[/cyan]")

        if deleted and any(deleted.values()):
            parts = []
            if deleted.get("evaluations"):
                parts.append(f"{deleted['evaluations']} evaluations")
            if deleted.get("guardrail_sets"):
                parts.append(f"{deleted['guardrail_sets']} guardrail sets")
            if deleted.get("guardrails"):
                parts.append(f"{deleted['guardrails']} guardrails")
            if parts:
                console.print(f"  Deleted: {', '.join(parts)}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@score_app.command("compare")
def score_compare(
    id1: str = typer.Argument(..., help="First score ID"),
    id2: str = typer.Argument(..., help="Second score ID"),
):
    """Compare two score runs"""
    console.print(f"[yellow]TODO:[/yellow] Compare '{id1}' vs '{id2}'")


# === GUARDRAILS ===


@guardrails_app.command("generate")
def guardrails_generate(
    score: str = typer.Argument(..., help="Score ID"),
    max_rules: int = typer.Option(3, "--max-rules", help="Max guardrails per failing criterion"),
    max_total: int = typer.Option(20, "--max-total", help="Max total guardrails across all criteria"),
):
    """Generate guardrails from score failures"""
    from srl4c.cli.commands.guardrails import generate_guardrails_cmd

    generate_guardrails_cmd(console, score, max_rules, max_total)


@guardrails_app.command("list")
def guardrails_list():
    """List generated guardrails"""
    from srl4c.cli.commands.guardrails import list_guardrails

    list_guardrails(console)


@guardrails_app.command("show")
def guardrails_show(set_id: str = typer.Argument(..., help="Guardrail set ID")):
    """Show all guardrails in a set"""
    from srl4c.cli.commands.guardrails import show_guardrail

    show_guardrail(console, set_id)


@guardrails_app.command("export")
def guardrails_export(set_id: str = typer.Argument(..., help="Guardrail set ID")):
    """Export guardrails as text for system prompt"""
    from srl4c.cli.commands.guardrails import export_guardrails

    export_guardrails(console, set_id)


@guardrails_app.command("delete")
def guardrails_delete(
    set_id: str = typer.Argument(..., help="Guardrail set ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a guardrail set and its rules"""
    from rich.prompt import Confirm

    from srl4c.db.repository import GuardrailSetRepository

    try:
        preview = GuardrailSetRepository.delete_preview(set_id)
        if preview is None:
            console.print(f"[red]Guardrail set not found: {set_id}[/red]")
            return

        gset = preview.get("guardrail_set", {})
        has_children = preview.get("has_children", False)
        will_delete = preview.get("will_delete", {})

        console.print(f"\n[bold]Delete Guardrail Set:[/bold] [cyan]{gset.get('id', set_id)[:8]}[/cyan]")
        if gset.get("rules_count"):
            console.print(f"  Rules: {gset['rules_count']}")

        if has_children:
            console.print("\n[yellow]⚠ This will also delete:[/yellow]")
            if will_delete.get("guardrails"):
                console.print(f"  • {will_delete['guardrails']} guardrail rule(s)")

        if not yes:
            confirm_text = "Delete ALL related data" if has_children else "Delete"
            if not Confirm.ask(f"\n{confirm_text}?"):
                console.print("[dim]Cancelled[/dim]")
                return

        deleted = GuardrailSetRepository.delete(set_id)
        console.print(f"\n[green]✓[/green] Deleted guardrail set [cyan]{set_id[:8]}[/cyan]")

        if deleted and deleted.get("guardrails"):
            console.print(f"  Deleted: {deleted['guardrails']} guardrails")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@guardrails_app.command("transform")
def guardrails_transform(
    input: str = typer.Option(..., "--input", "-i", help="Original system prompt"),
    guardrails: str = typer.Option(..., "--guardrails", "-g", help="Comma-separated guardrail IDs"),
):
    """Transform a system prompt by adding guardrails"""
    console.print(f"[yellow]TODO:[/yellow] Transform prompt with guardrails '{guardrails}'")


@guardrails_app.command("deploy")
def guardrails_deploy_cmd(
    set_id: str = typer.Argument(..., help="Guardrail set ID to deploy"),
):
    """Deploy guardrails as a Cloudflare Worker proxy"""
    from srl4c.cli.commands.guardrails import deploy_guardrails

    deploy_guardrails(console, set_id)


@guardrails_app.command("worker")
def guardrails_worker(
    set_id: str = typer.Argument(..., help="Guardrail set ID"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate Cloudflare Worker code (without deploying)"""
    from srl4c.cli.commands.guardrails import generate_worker

    generate_worker(console, set_id, output)


# === PRINCIPLES ===


@principles_app.command("list")
def principles_list():
    """List all design principles"""
    from srl4c.cli.commands.principles import list_principles

    list_principles(console)


@principles_app.command("show")
def principles_show(id: str = typer.Argument(..., help="Principle ID or name")):
    """Show principle details"""
    from srl4c.cli.commands.principles import show_principle

    show_principle(console, id)


@principles_app.command("add")
def principles_add(file: Path = typer.Argument(..., help="Path to .prompt file")):
    """Add a custom principle"""
    console.print(f"[yellow]TODO:[/yellow] Add principle from '{file}'")


@principles_app.command("validate")
def principles_validate(file: Path = typer.Argument(..., help="Path to .prompt file")):
    """Validate a principle file"""
    console.print(f"[yellow]TODO:[/yellow] Validate principle '{file}'")


# === JUDGES ===


@judges_app.command("list")
def judges_list():
    """List available judge configurations"""
    from rich.table import Table

    from srl4c.judge.config import list_judge_files

    files = list_judge_files()

    if not files:
        console.print("[dim]No judge configurations found. Run 'srl4c init' first.[/dim]")
        return

    table = Table(show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Judges")
    table.add_column("Passes")
    table.add_column("Active")

    for f in files:
        active = "[green]✓[/green]" if f["is_active"] else ""
        table.add_row(
            f["name"],
            str(f["judges_count"]),
            str(f["n_passes"]),
            active,
        )

    console.print(table)


@judges_app.command("use")
def judges_use(
    name: str = typer.Argument(..., help="Judge config filename (e.g. default.judges)"),
):
    """Switch to a different judge configuration"""
    from srl4c.judge.config import list_judge_files, set_active_judges

    # Ensure .judges extension
    if not name.endswith(".judges"):
        name = f"{name}.judges"

    # Check if file exists
    files = list_judge_files()
    names = [f["name"] for f in files]

    if name not in names:
        console.print(f"[red]Judge config not found: {name}[/red]")
        console.print(f"[dim]Available: {', '.join(names)}[/dim]")
        return

    set_active_judges(name)
    console.print(f"[green]✓[/green] Now using [cyan]{name}[/cyan]")


@judges_app.command("show")
def judges_show(
    name: str = typer.Argument(None, help="Judge config filename (default: active config)"),
):
    """Show contents of a judge configuration"""
    from srl4c.judge.config import get_active_judges_file, get_judge_file_content

    if name is None:
        name = get_active_judges_file()
    elif not name.endswith(".judges"):
        name = f"{name}.judges"

    content = get_judge_file_content(name)

    if content is None:
        console.print(f"[red]Judge config not found: {name}[/red]")
        return

    console.print(f"[bold]Judge Config: {name}[/bold]\n")
    console.print(content)


@judges_app.command("test")
def judges_test():
    """Test connectivity to all configured judges"""
    from rich.table import Table

    from srl4c.judge.config import get_active_judges_file, test_all_judges

    console.print(f"Testing judges from [cyan]{get_active_judges_file()}[/cyan]...\n")

    results = test_all_judges()

    if not results:
        console.print("[yellow]No judges configured[/yellow]")
        return

    table = Table(show_edge=False)
    table.add_column("Judge", style="bold")
    table.add_column("Model")
    table.add_column("Status")
    table.add_column("Response Time")

    for r in results:
        if r["success"]:
            status = "[green]✓ OK[/green]"
            time_str = f"{r['response_time_ms']}ms"
        else:
            status = f"[red]✗ {r['error']}[/red]"
            time_str = "-"

        table.add_row(r["name"], r["model"], status, time_str)

    console.print(table)


# === GENERATORS ===


@generators_app.command("list")
def generators_list():
    """List available generator configurations"""
    from rich.table import Table

    from srl4c.generator.config import list_generator_files

    files = list_generator_files()

    if not files:
        console.print("[dim]No generator configurations found. Run 'srl4c init' first.[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("Name", style="bold")
    table.add_column("Model")
    table.add_column("Active")

    for f in files:
        active = "[green]✓[/green]" if f["is_active"] else ""
        table.add_row(f["name"], f["model"], active)

    console.print(table)


@generators_app.command("use")
def generators_use(
    name: str = typer.Argument(..., help="Generator config filename (e.g. default.generators)"),
):
    """Switch to a different generator configuration"""
    from srl4c.generator.config import list_generator_files, set_active_generators

    if not name.endswith(".generators"):
        name = f"{name}.generators"

    files = list_generator_files()
    names = [f["name"] for f in files]

    if name not in names:
        console.print(f"[red]Generator config not found: {name}[/red]")
        console.print(f"[dim]Available: {', '.join(names)}[/dim]")
        return

    set_active_generators(name)
    console.print(f"[green]✓[/green] Now using [cyan]{name}[/cyan]")


@generators_app.command("show")
def generators_show(
    name: str = typer.Argument(None, help="Generator config filename (default: active config)"),
):
    """Show contents of a generator configuration"""
    from srl4c.generator.config import (
        get_active_generators_file,
        get_generator_file_content,
    )

    if name is None:
        name = get_active_generators_file()
    elif not name.endswith(".generators"):
        name = f"{name}.generators"

    content = get_generator_file_content(name)

    if content is None:
        console.print(f"[red]Generator config not found: {name}[/red]")
        return

    console.print(f"[bold]Generator Config: {name}[/bold]\n")
    console.print(content)


@generators_app.command("test")
def generators_test():
    """Test connectivity to the active generator"""
    from rich.table import Table

    from srl4c.generator.config import get_active_generators_file, test_active_generator

    console.print(f"Testing generator from [cyan]{get_active_generators_file()}[/cyan]...\n")

    r = test_active_generator()

    table = Table(show_edge=False)
    table.add_column("Generator", style="bold")
    table.add_column("Model")
    table.add_column("Status")
    table.add_column("Response Time")

    if r["success"]:
        status = "[green]✓ OK[/green]"
        time_str = f"{r['response_time_ms']}ms"
    else:
        status = f"[red]✗ {r['error']}[/red]"
        time_str = "-"

    table.add_row(r["name"], r["model"], status, time_str)
    console.print(table)


# === CONFIG ===


@config_app.command("show")
def config_show():
    """Show current configuration"""
    console.print("[yellow]TODO:[/yellow] Show config")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. output.format)"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value"""
    console.print(f"[yellow]TODO:[/yellow] Set {key}={value}")


@config_app.command("edit")
def config_edit():
    """Open config in editor"""
    console.print("[yellow]TODO:[/yellow] Open config in $EDITOR")


# === API ===

api_app = typer.Typer(help="API server commands")
app.add_typer(api_app, name="api")


@api_app.command("serve")
def api_serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the API server"""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]uvicorn not installed. Run: uv add uvicorn[/red]")
        return

    console.print("\n[bold]Starting SRL4C API server[/bold]")
    console.print(f"  Host: [cyan]{host}[/cyan]")
    console.print(f"  Port: [cyan]{port}[/cyan]")
    console.print(f"  Docs: [cyan]http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs[/cyan]\n")

    uvicorn.run(
        "srl4c.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
