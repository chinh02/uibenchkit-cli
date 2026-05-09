"""
List runs from the UIBenchKit API server.
"""
import requests
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="List all existing runs", name="list-runs")


def list_runs(
    model: Optional[str] = typer.Option(
        None,
        '--model', '-m',
        help="Filter by model (family or version)"
    ),
    method: Optional[str] = typer.Option(
        None,
        '--method',
        help="Filter by method (dcgen, direct, latcoder, uicopilot, layoutcoder)"
    ),
    dataset: Optional[str] = typer.Option(
        None,
        '--dataset', '-d',
        help="Filter by dataset (design2code, dcgen)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """List all existing runs in your account."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    # Build filter payload
    payload = {}
    if model:
        payload["model"] = model
    if method:
        payload["method"] = method
    if dataset:
        payload["dataset"] = dataset
    
    with console.status("[blue]Fetching runs..."):
        response = requests.post(
            f"{API_BASE_URL}/list-runs",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    
    runs = result.get('runs', [])
    
    if len(runs) == 0:
        filters = []
        if model:
            filters.append(f"model={model}")
        if method:
            filters.append(f"method={method}")
        if dataset:
            filters.append(f"dataset={dataset}")
        filter_str = " with " + ", ".join(filters) if filters else ""
        console.print(f"[yellow]No runs found{filter_str}[/]")
        return
    
    # Create a rich table
    table = Table(title=f"Runs ({len(runs)} total)")
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Model", style="green")
    table.add_column("Method", style="magenta")
    table.add_column("Dataset", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for run in runs:
        status = run.get('status', 'unknown')
        status_style = {
            'completed': '[green]completed[/]',
            'running': '[yellow]running[/]',
            'pending': '[blue]pending[/]',
            'failed': '[red]failed[/]'
        }.get(status, status)
        
        table.add_row(
            run.get('run_id', 'N/A'),
            run.get('model', 'N/A'),
            run.get('method', 'N/A'),
            run.get('dataset', 'N/A') or 'custom',
            status_style,
            run.get('created_at', 'N/A')[:19] if run.get('created_at') else 'N/A'
        )
    
    console.print(table)


if __name__ == "__main__":
    app()

