"""Guardrails commands - generate and manage safety guardrails"""

import subprocess
import shutil
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from srl4c.db.models import db_connection
from srl4c.db.repository import GuardrailSetRepository


def generate_guardrails_cmd(console: Console, score_id: str, max_rules: int = 3, max_total: int = 20):
    """Generate guardrails from score failures"""
    from srl4c.core.guardrails import (
        create_guardrails, run_guardrails, get_guardrails_details, load_guardrails_config
    )

    # Create guardrail set (shared with API)
    try:
        set_id = create_guardrails(score_id, max_rules=max_rules, max_total=max_total)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Get details for display
    details = get_guardrails_details(set_id)
    if not details:
        console.print(f"[red]Error: Could not get guardrail set details[/red]")
        return

    config = load_guardrails_config()

    console.print(f"\nAnalyzing {details['failing_principles_count']} failing principles from score [cyan]{score_id}[/cyan]...")
    console.print(f"Using [cyan]{config.get('model', 'gpt-4o-mini')}[/cyan] for guardrail generation\n")
    console.print(f"Guardrail set [cyan]{set_id}[/cyan] created\n")

    # Run with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating guardrails...", total=details['failing_principles_count'])

        def on_progress(current: int, total: int):
            progress.update(task, completed=current, total=total)

        try:
            all_guardrails = run_guardrails(set_id, max_rules=max_rules, max_total=max_total, on_progress=on_progress)
        except ValueError as e:
            console.print(f"\n[yellow]{e}[/yellow]")
            return
        except Exception as e:
            console.print(f"\n[red]✗[/red] Guardrail generation failed: {e}")
            return

    # Display results
    console.print(f"\n[green]✓[/green] Generated {len(all_guardrails)} guardrails in set [cyan]{set_id}[/cyan]\n")

    console.print("═" * 75)
    console.print(f"[bold]              GUARDRAIL SET: {set_id} (from score {score_id[:8]})[/bold]")
    console.print("═" * 75)
    console.print()

    table = Table(show_edge=False)
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Principle", no_wrap=True)
    table.add_column("Rule")

    for idx, g in enumerate(all_guardrails, 1):
        short_p = g['criteria_id'].split(".")[-1]
        table.add_row(
            str(idx),
            short_p,
            g['rule_text'][:70] + "..." if len(g['rule_text']) > 70 else g['rule_text']
        )

    console.print(table)
    console.print()
    console.print("Next steps:")
    console.print(f"  [cyan]srl4c guardrails list[/cyan]           # View all guardrail sets")
    console.print(f"  [cyan]srl4c guardrails show {set_id}[/cyan]   # Show rules in this set")
    console.print(f"  [cyan]srl4c guardrails export {set_id}[/cyan] # Export as text")


def list_guardrails(console: Console):
    """List all guardrail sets"""
    with db_connection() as conn:
        rows = conn.execute(
            """SELECT gs.*, s.attack_id, e.name as endpoint_name
               FROM guardrail_sets gs
               JOIN scores s ON gs.score_id = s.id
               JOIN attacks a ON s.attack_id = a.id
               JOIN endpoints e ON a.endpoint_id = e.id
               ORDER BY gs.created_at DESC"""
        ).fetchall()

    if not rows:
        console.print("[dim]No guardrail sets yet. Use 'srl4c guardrails generate <score-id>' to generate.[/dim]")
        return

    table = Table(show_edge=False)
    table.add_column("Set ID", style="cyan", no_wrap=True)
    table.add_column("Endpoint", style="bold", no_wrap=True)
    table.add_column("Attack", no_wrap=True)
    table.add_column("Score", no_wrap=True)
    table.add_column("Model", no_wrap=True)
    table.add_column("Rules", justify="right", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Date", style="dim", no_wrap=True)

    for row in rows:
        date = row['created_at'][:10] if row['created_at'] else ""
        model_short = row['model'].split("/")[-1] if row['model'] else ""

        # Status styling
        status = row['status'] or 'completed'
        if status == "completed":
            status_color = "green"
        elif status == "failed":
            status_color = "red"
        elif status == "running":
            status_color = "yellow"
        else:
            status_color = "dim"

        table.add_row(
            row['id'][:8],
            row['endpoint_name'],
            row['attack_id'][:8],
            row['score_id'][:8],
            model_short,
            str(row['rules_count']),
            f"[{status_color}]{status}[/{status_color}]",
            date,
        )

    console.print(table)


def show_guardrail(console: Console, set_id: str):
    """Show all guardrails in a set"""
    gset = GuardrailSetRepository.get_by_id(set_id)

    if not gset:
        console.print(f"[red]Guardrail set not found: {set_id}[/red]")
        return

    with db_connection() as conn:
        guardrails = conn.execute(
            "SELECT * FROM guardrails WHERE set_id = ? ORDER BY created_at",
            (gset['id'],)
        ).fetchall()

    console.print()
    console.print("═" * 75)
    console.print(f"[bold]              GUARDRAIL SET: {gset['id']}[/bold]")
    console.print("═" * 75)
    console.print(f"Score: {gset['score_id']}")
    console.print(f"Model: {gset['model']}")
    console.print(f"Status: {gset['status'] or 'completed'}")
    if gset.get('error_message'):
        console.print(f"Error: [red]{gset['error_message']}[/red]")
    console.print(f"Created: {gset['created_at']}")
    console.print(f"Rules: {gset['rules_count']}")
    console.print()

    for idx, g in enumerate(guardrails, 1):
        short_p = g['criteria_id'].split(".")[-1] if g['criteria_id'] else ""
        console.print(f"[bold]Rule {idx}[/bold] - {short_p}")
        console.print(f"  {g['rule_text']}")
        if g['rationale']:
            console.print(f"  [dim]Rationale: {g['rationale']}[/dim]")
        console.print()


def export_guardrails(console: Console, set_id: str):
    """Export all guardrails in a set as text for system prompt"""
    gset = GuardrailSetRepository.get_by_id(set_id)

    if not gset:
        console.print(f"[red]Guardrail set not found: {set_id}[/red]")
        return

    with db_connection() as conn:
        guardrails = conn.execute(
            "SELECT * FROM guardrails WHERE set_id = ? ORDER BY created_at",
            (gset['id'],)
        ).fetchall()

    if not guardrails:
        console.print("[yellow]No guardrails in this set[/yellow]")
        return

    console.print(f"\nExporting guardrail set [cyan]{gset['id']}[/cyan] ({len(guardrails)} rules)")
    console.print()
    console.print("Add these rules to your system prompt:")
    console.print("─" * 70)
    console.print()
    for g in guardrails:
        console.print(f"- {g['rule_text']}")
    console.print()
    console.print("─" * 70)


WORKER_TEMPLATE = '''// SRL4C Guardrail Proxy Worker
// Generated for guardrail set: {set_id}
// Rules: {rules_count}

const GUARDRAILS = `
IMPORTANT SAFETY RULES - You MUST follow these:
{guardrails_text}
`;

export default {{
  async fetch(request, env) {{
    // CORS preflight
    if (request.method === 'OPTIONS') {{
      return new Response(null, {{
        headers: {{
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }},
      }});
    }}

    if (request.method !== 'POST') {{
      return new Response(JSON.stringify({{ error: 'Method not allowed' }}), {{
        status: 405,
        headers: {{ 'Content-Type': 'application/json' }},
      }});
    }}

    try {{
      const body = await request.json();

      // Extract target and api_key from body
      const target = body._target || 'https://api.openai.com/v1';
      const apiKey = body._api_key;

      delete body._target;
      delete body._api_key;

      if (!apiKey) {{
        return new Response(JSON.stringify({{ error: 'No API key provided in _api_key field' }}), {{
          status: 400,
          headers: {{ 'Content-Type': 'application/json' }},
        }});
      }}

      // Inject guardrails into messages
      if (body.messages && Array.isArray(body.messages)) {{
        if (body.messages[0]?.role === 'system') {{
          body.messages[0].content = GUARDRAILS + '\\n\\n' + body.messages[0].content;
        }} else {{
          body.messages.unshift({{ role: 'system', content: GUARDRAILS }});
        }}
      }}

      // Forward to target - always use /chat/completions
      const targetUrl = target.replace(/\\/+$/, '') + '/chat/completions';

      const response = await fetch(targetUrl, {{
        method: 'POST',
        headers: {{
          'Authorization': `Bearer ${{apiKey}}`,
          'Content-Type': 'application/json',
        }},
        body: JSON.stringify(body),
      }});

      const responseBody = await response.text();
      return new Response(responseBody, {{
        status: response.status,
        headers: {{
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        }},
      }});

    }} catch (error) {{
      return new Response(JSON.stringify({{ error: error.message }}), {{
        status: 500,
        headers: {{ 'Content-Type': 'application/json' }},
      }});
    }}
  }},
}};
'''


def generate_worker(console: Console, set_id: str, output_path: str = None):
    """Generate Cloudflare Worker code with guardrails baked in"""
    gset = GuardrailSetRepository.get_by_id(set_id)

    if not gset:
        console.print(f"[red]Guardrail set not found: {set_id}[/red]")
        return None

    with db_connection() as conn:
        guardrails = conn.execute(
            "SELECT * FROM guardrails WHERE set_id = ? ORDER BY created_at",
            (gset['id'],)
        ).fetchall()

    if not guardrails:
        console.print("[yellow]No guardrails in this set[/yellow]")
        return None

    # Format guardrails as bullet points
    guardrails_text = "\n".join(f"- {g['rule_text']}" for g in guardrails)

    # Generate worker code
    worker_code = WORKER_TEMPLATE.format(
        set_id=gset['id'][:8],
        rules_count=len(guardrails),
        guardrails_text=guardrails_text
    )

    if output_path:
        Path(output_path).write_text(worker_code)
        console.print(f"[green]✓[/green] Worker code written to {output_path}")
    else:
        console.print(worker_code)

    return worker_code, gset['id']


def deploy_guardrails(console: Console, set_id: str):
    """Deploy guardrails as a Cloudflare Worker"""
    import re

    # Generate worker code
    result = generate_worker(console, set_id)
    if not result:
        return

    worker_code, full_set_id = result
    short_id = full_set_id[:8]

    console.print(f"\n[bold]Deploying guardrail set {short_id} to Cloudflare Workers[/bold]\n")

    # Check wrangler
    if not shutil.which("wrangler") and not shutil.which("npx"):
        console.print("[red]wrangler not found. Install with: npm install -g wrangler[/red]")
        return

    wrangler_cmd = ["wrangler"] if shutil.which("wrangler") else ["npx", "wrangler"]

    # Check login
    try:
        result = subprocess.run(
            wrangler_cmd + ["whoami"],
            capture_output=True, text=True, timeout=10
        )
        if "not authenticated" in result.stdout.lower() or result.returncode != 0:
            console.print("[yellow]Not logged in. Running wrangler login...[/yellow]")
            subprocess.run(wrangler_cmd + ["login"])
    except Exception as e:
        console.print(f"[yellow]Could not check login: {e}[/yellow]")

    console.print("[green]✓[/green] Wrangler ready")

    # Create temp directory with worker files
    with tempfile.TemporaryDirectory() as tmpdir:
        worker_path = Path(tmpdir) / "worker.js"
        toml_path = Path(tmpdir) / "wrangler.toml"

        worker_path.write_text(worker_code)
        toml_path.write_text(f'''name = "srl4c-guard-{short_id}"
main = "worker.js"
compatibility_date = "2024-01-01"
''')

        console.print("[dim]Deploying...[/dim]")

        try:
            result = subprocess.run(
                wrangler_cmd + ["deploy"],
                cwd=tmpdir,
                capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                console.print(f"[red]Deploy failed:[/red]\n{result.stderr}")
                return

            # Extract URL
            match = re.search(r'https://[^\s]+workers\.dev', result.stdout)
            worker_url = match.group(0) if match else f"https://srl4c-guard-{short_id}.<your-subdomain>.workers.dev"

            console.print()
            console.print("═" * 60)
            console.print(f"[bold green]✓ Deployed![/bold green]")
            console.print()
            console.print(f"  Worker URL: [cyan]{worker_url}[/cyan]")
            console.print()
            console.print("  [bold]To use in Python:[/bold]")
            console.print(f'    [dim]export SRL4C_WORKER_URL="{worker_url}"[/dim]')
            console.print(f"    [dim]client = srl4c(OpenAI(api_key='sk-...', base_url='...'))[/dim]")
            console.print("═" * 60)

        except subprocess.TimeoutExpired:
            console.print("[red]Deployment timed out[/red]")
        except Exception as e:
            console.print(f"[red]Deployment failed: {e}[/red]")
