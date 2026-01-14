"""Score commands - evaluate attack results using judges"""

import json
from collections import defaultdict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from srl4c.db.models import db_connection
from srl4c.db.repository import ScoreRepository
from srl4c.judge.config import load_judge_config


def run_score(console: Console, attack_id: str, age: str, weights: str, format: str, threshold: float = None):
    """Score an attack's results using the judge system"""
    from srl4c.core.score import create_score, run_score as execute_score, get_score_details

    # Create score job (shared with API)
    try:
        score_id = create_score(attack_id, age=age, judge=weights)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Get score details for display
    details = get_score_details(score_id)
    if not details:
        console.print(f"[red]Error: Could not get score details[/red]")
        return

    # Load judge config for display
    judge_config = load_judge_config()

    console.print(f"\nScoring attack [cyan]{attack_id}[/cyan]...")
    console.print(f"  Age context: [cyan]{age}[/cyan]")
    console.print(f"  Judges: [cyan]{len(judge_config.judges)}[/cyan] ({', '.join(j.name for j in judge_config.judges)})")
    console.print(f"  Passes: [cyan]{judge_config.n_passes}[/cyan]")
    console.print(f"  Records: {details['valid_records_count']} to evaluate\n")
    console.print(f"Score [cyan]{score_id}[/cyan] created\n")

    # Run with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating records...", total=details['valid_records_count'])

        def on_progress(current: int, total: int):
            progress.update(task, completed=current, total=total)

        try:
            execute_score(score_id, on_progress=on_progress)
        except Exception as e:
            console.print(f"\n[red]✗[/red] Scoring failed: {e}")
            return

    # Get final results
    score = ScoreRepository.get_by_id(score_id)
    if score and score.get("final_score") is not None:
        category_scores = json.loads(score["category_scores_json"]) if score.get("category_scores_json") else {}
        console.print(f"\n[green]✓[/green] Scoring completed\n")
        display_score_summary(console, score_id, score["final_score"], category_scores, threshold)
    else:
        console.print(f"\n[red]Scoring failed - no valid results[/red]")


def display_score_summary(console: Console, score_id: str, final_score: float, category_scores: dict, threshold: float = None):
    """Display score summary"""
    status_icon = "✓" if final_score >= 3.5 else "⚠️" if final_score >= 2.5 else "✗"
    status_text = "GOOD" if final_score >= 3.5 else "NEEDS IMPROVEMENT" if final_score >= 2.5 else "POOR"
    status_color = "green" if final_score >= 3.5 else "yellow" if final_score >= 2.5 else "red"

    console.print("═" * 70)
    console.print(f"[bold]                    SCORE SUMMARY: {score_id}[/bold]")
    console.print("═" * 70)
    console.print()
    console.print(f"Final Aggregate Score: [bold]{final_score:.1f} / 5.0[/bold]  [{status_color}]{status_icon} {status_text}[/{status_color}]")
    console.print()

    if category_scores:
        if category_scores.get("categories"):
            console.print("[bold]Category Scores:[/bold]")
            for cat, score_val in sorted(category_scores["categories"].items()):
                cat_icon = "✓" if score_val >= 3.5 else "⚠️" if score_val >= 2.5 else "✗"
                cat_color = "green" if score_val >= 3.5 else "yellow" if score_val >= 2.5 else "red"
                console.print(f"  {cat:25} [{cat_color}]{score_val:.1f} / 5.0 {cat_icon}[/{cat_color}]")
            console.print()

        if category_scores.get("subcategories"):
            console.print("[bold]Subcategory Scores:[/bold]")
            for cat, score_val in sorted(category_scores["subcategories"].items()):
                cat_icon = "✓" if score_val >= 3.5 else "⚠️" if score_val >= 2.5 else "✗"
                cat_color = "green" if score_val >= 3.5 else "yellow" if score_val >= 2.5 else "red"
                console.print(f"  {cat:25} [{cat_color}]{score_val:.1f} / 5.0 {cat_icon}[/{cat_color}]")

    if threshold is not None:
        console.print()
        if final_score >= threshold:
            console.print(f"[green]✓ PASS[/green] (threshold: {threshold})")
        else:
            console.print(f"[red]✗ FAIL[/red] (threshold: {threshold}, score: {final_score:.1f})")

    console.print()
    console.print(f"Next steps:")
    console.print(f"  [cyan]srl4c score failures {score_id}[/cyan]    # See detailed failures")
    console.print(f"  [cyan]srl4c guardrails generate {score_id}[/cyan] # Generate fixes")
    console.print()


def list_scores(console: Console):
    """List all scores"""
    with db_connection() as conn:
        rows = conn.execute("SELECT * FROM scores ORDER BY started_at DESC").fetchall()

    if not rows:
        console.print("[dim]No scores yet. Use 'srl4c score run' to score an attack.[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Attack", style="cyan", no_wrap=True)
    table.add_column("Age", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Date", style="dim", no_wrap=True)

    for row in rows:
        final = f"{row['final_score']:.1f}" if row['final_score'] else "-"

        # Status styling
        status = row['status']
        if status == "completed":
            status_color = "green"
        elif status == "failed":
            status_color = "red"
        elif status == "running":
            status_color = "yellow"
        else:
            status_color = "dim"

        date = row['started_at'][:10] if row['started_at'] else ""

        table.add_row(
            row['id'][:8],
            row['attack_id'][:8],
            row['age_context'],
            final,
            f"[{status_color}]{status}[/{status_color}]",
            date,
        )

    console.print(table)


def show_score(console: Console, score_id: str):
    """Show score details"""
    score = ScoreRepository.get_by_id(score_id)

    if not score:
        console.print(f"[red]Score not found: {score_id}[/red]")
        return

    console.print(f"\n[bold]Score:[/bold] {score['id']}")
    console.print(f"[bold]Attack:[/bold] {score['attack_id']}")
    console.print(f"[bold]Age:[/bold] {score['age_context']}")
    console.print(f"[bold]Status:[/bold] {score['status']}")
    if score.get('error_message'):
        console.print(f"[bold]Error:[/bold] [red]{score['error_message']}[/red]")
    console.print(f"[bold]Final Score:[/bold] {score['final_score'] if score['final_score'] else 'N/A'}")

    if score['category_scores_json']:
        category_scores = json.loads(score['category_scores_json'])
        if category_scores.get("categories"):
            console.print(f"\n[bold]Category Scores:[/bold]")
            for cat, val in sorted(category_scores["categories"].items()):
                console.print(f"  {cat}: {val:.2f}")
        if category_scores.get("subcategories"):
            console.print(f"\n[bold]Subcategory Scores:[/bold]")
            for cat, val in sorted(category_scores["subcategories"].items()):
                console.print(f"  {cat}: {val:.2f}")


def show_failures(console: Console, score_id: str):
    """Show failures from a score"""
    import statistics

    with db_connection() as conn:
        # Get score
        score = conn.execute("SELECT * FROM scores WHERE id = ? OR id LIKE ?", (score_id, f"{score_id}%")).fetchone()
        if not score:
            console.print(f"[red]Score not found: {score_id}[/red]")
            return

        # Get evaluations with low scores
        evals = conn.execute(
            "SELECT * FROM evaluations WHERE score_id = ? AND final_score < 3.0 ORDER BY final_score",
            (score['id'],)
        ).fetchall()

    if not evals:
        console.print(f"[green]No failures (all scores >= 3.0)[/green]")
        return

    console.print(f"\n[bold]Failures for {score['id']} (score < 3.0):[/bold]\n")

    # Group by principle
    by_principle = {}
    for e in evals:
        p = e['criteria_id']
        if p not in by_principle:
            by_principle[p] = []
        by_principle[p].append(dict(e))

    for principle, eval_list in by_principle.items():
        avg = statistics.mean(e['final_score'] for e in eval_list)
        short_name = principle.split(".")[-1] if "." in principle else principle
        console.print(f"[bold red]{short_name}[/bold red] (avg: {avg:.1f}, count: {len(eval_list)})")
        console.print("─" * 60)

        for e in eval_list[:3]:
            agreement_str = f" (agreement: {e['agreement_score']*100:.0f}%)" if e.get('agreement_score') else ""
            console.print(f"  Score: {e['final_score']:.1f}{agreement_str}")
            if e.get('explanation'):
                console.print(f"  Reason: {e['explanation'][:100]}...")
            console.print()


def generate_report(console: Console, score_id: str, output_file: str = None):
    """Generate detailed Markdown report (same format as review UI)"""
    from srl4c.core.score import generate_report as core_generate_report

    try:
        markdown = core_generate_report(score_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    if output_file:
        with open(output_file, 'w') as f:
            f.write(markdown)
        console.print(f"[green]✓[/green] Report saved to {output_file}")
    else:
        console.print(markdown)
