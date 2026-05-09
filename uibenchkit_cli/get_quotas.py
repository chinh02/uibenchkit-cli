"""
Get API quotas from the UIBenchKit API server.
"""
import requests
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Get remaining quota counts for your API key")


def get_quotas(
    api_key: Optional[str] = typer.Option(
        None, 
        '--api-key', '-k',
        help="API key", 
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """Get remaining quota counts for all model families."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}

    with console.status("[blue]Fetching quota information..."):
        response = requests.get(f"{API_BASE_URL}/get-quotas", headers=headers)
        verify_response(response)
        result = response.json()

    # Create a rich table to display the quotas
    table = Table(title="Remaining Submission Quotas")
    table.add_column("Model Family", style="cyan")
    table.add_column("Remaining Runs", style="green", justify="right")

    quotas = result.get("remaining_quotas", {})
    if not quotas:
        console.print("[yellow]No quota information available[/]")
        return

    # Add rows to the table
    for model_family, info in quotas.items():
        if isinstance(info, dict):
            runs = info.get('runs', 'N/A')
        else:
            runs = info
        table.add_row(model_family, str(runs))

    console.print(table)


if __name__ == "__main__":
    app()

