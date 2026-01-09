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
config_app = typer.Typer(help="Manage configuration")

app.add_typer(endpoint_app, name="endpoint")
app.add_typer(dataset_app, name="dataset")
app.add_typer(attack_app, name="attack")
app.add_typer(score_app, name="score")
app.add_typer(guardrails_app, name="guardrails")
app.add_typer(principles_app, name="principles")
app.add_typer(config_app, name="config")


# === INIT ===

@app.command()
def init():
    """Initialize SRL4C - create ~/.srl4c/ directory structure"""
    from srl4c.cli.commands.init import run_init
    run_init(console)


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
def endpoint_remove(id: str = typer.Argument(..., help="Endpoint ID or name")):
    """Remove an endpoint"""
    from srl4c.cli.commands.endpoint import remove_endpoint
    remove_endpoint(console, id)


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


@guardrails_app.command("transform")
def guardrails_transform(
    input: str = typer.Option(..., "--input", "-i", help="Original system prompt"),
    guardrails: str = typer.Option(..., "--guardrails", "-g", help="Comma-separated guardrail IDs"),
):
    """Transform a system prompt by adding guardrails"""
    console.print(f"[yellow]TODO:[/yellow] Transform prompt with guardrails '{guardrails}'")


@guardrails_app.command("deploy")
def guardrails_deploy_cmd(set_id: str = typer.Argument(..., help="Guardrail set ID to deploy")):
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


if __name__ == "__main__":
    app()
