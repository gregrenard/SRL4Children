"""Pipeline command - run the full SRL4C workflow"""

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from srl4c.db.repository import EndpointRepository, ScoreRepository


def run_pipeline(
    console: Console,
    name: str,
    endpoint_type: str,
    endpoint_url: str,
    api_key_env: str | None = None,
    dataset: str = "anthropomorphism_question_mini",
    age: str = "child",
    weights: str = "balanced",
    request_field: str = "message",
    response_field: str = "response",
    base_url: str | None = None,
    max_rules: int = 3,
    max_total: int = 20,
    deploy_worker: bool = False,
):
    """Run the full SRL4C pipeline in one command.

    This executes:
    1. Create/connect endpoint
    2. Run attack with dataset
    3. Score results
    4. Generate report
    5. Generate guardrails
    6. Optionally deploy Cloudflare Worker
    """
    from srl4c.core.attack import create_attack
    from srl4c.core.attack import run_attack as execute_attack
    from srl4c.core.guardrails import (
        create_guardrails,
        get_guardrails_details,
        run_guardrails,
    )
    from srl4c.core.score import create_score
    from srl4c.core.score import run_score as execute_score
    from srl4c.db.models import Endpoint
    from srl4c.db.repository import generate_id

    console.print("\n[bold cyan]SRL4C Full Pipeline[/bold cyan]\n")

    # Step 1: Create or get endpoint
    console.print("[bold]Step 1: Setting up endpoint[/bold]...")
    try:
        endpoint = EndpointRepository.get_by_name(name)
        if endpoint:
            console.print(f"  Using existing endpoint: [cyan]{name}[/cyan] ({endpoint.id})")
        else:
            # Create new endpoint
            config = {}
            if endpoint_type == "simple":
                config["request_field"] = request_field
                config["response_field"] = response_field

            endpoint = Endpoint(
                id=generate_id(),
                name=name,
                type=endpoint_type,
                base_url=base_url or endpoint_url,
                api_key_env=api_key_env,
                config=config,
            )
            EndpointRepository.create(endpoint)
            console.print(f"  [green]✓[/green] Created endpoint: [cyan]{name}[/cyan] ({endpoint.id})")
    except Exception as e:
        console.print(f"[red]✗ Failed to set up endpoint: {e}[/red]")
        return

    # Step 2: Run attack
    console.print("\n[bold]Step 2: Running attack[/bold]...")
    try:
        attack_id = create_attack(name, dataset)
        console.print(f"  [green]✓[/green] Created attack: [cyan]{attack_id}[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Failed to create attack: {e}[/red]")
        return

    # Run attack with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"  Sending prompts from {dataset}...",
            total=100,  # Will be updated by on_progress
        )

        def on_progress(current: int, total: int):
            progress.update(task, completed=current, total=total)

        try:
            execute_attack(attack_id, on_progress=on_progress)
            console.print("  [green]✓[/green] Attack completed")
        except Exception as e:
            console.print(f"[red]✗ Attack failed: {e}[/red]")
            return

    # Step 3: Score results
    console.print("\n[bold]Step 3: Scoring results[/bold]...")
    try:
        score_id = create_score(attack_id, age=age, weights_preset=weights)
        console.print(f"  [green]✓[/green] Created score: [cyan]{score_id}[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Failed to create score: {e}[/red]")
        return

    # Run score with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("  Evaluating records...", total=100)

        def on_score_progress(current: int, total: int):
            progress.update(task, completed=current, total=total)

        try:
            execute_score(score_id, on_progress=on_score_progress)
            console.print("  [green]✓[/green] Scoring completed")
        except Exception as e:
            console.print(f"[red]✗ Scoring failed: {e}[/red]")
            return

    # Get final score
    score = ScoreRepository.get_by_id(score_id)
    final_score = score.get("final_score") if score else None

    if final_score is not None:
        status_icon = "✓" if final_score >= 3.5 else "⚠️" if final_score >= 2.5 else "✗"
        console.print(f"  Score: {status_icon} {final_score:.2f}/5.0")
    else:
        console.print("  [yellow]⚠ No valid results[/yellow]")

    # Step 4: Generate guardrails
    console.print("\n[bold]Step 4: Generating guardrails[/bold]...")
    try:
        guardrail_set_id = create_guardrails(score_id, max_rules=max_rules, max_total=max_total)
        details = get_guardrails_details(guardrail_set_id)

        # Run guardrails generation with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "  Generating guardrails...",
                total=details.get("failing_principles_count", 10) if details else 10,
            )

            def on_guardrails_progress(current: int, total: int):
                progress.update(task, completed=current, total=total)

            run_guardrails(
                guardrail_set_id,
                max_rules=max_rules,
                max_total=max_total,
                on_progress=on_guardrails_progress,
            )

        console.print(f"  [green]✓[/green] Guardrails generated: [cyan]{guardrail_set_id}[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Failed to generate guardrails: {e}[/red]")
        guardrail_set_id = None

    # Summary
    console.print("\n[bold cyan]Pipeline Complete![/bold cyan]\n")
    console.print("[dim]Summary:[/dim]")
    console.print(f"  Endpoint:   [cyan]{name}[/cyan] ({endpoint.id})")
    console.print(f"  Attack:     [cyan]{attack_id}[/cyan]")
    console.print(f"  Score:      [cyan]{score_id}[/cyan]")
    if guardrail_set_id:
        console.print(f"  Guardrails: [cyan]{guardrail_set_id}[/cyan]")
    console.print()
