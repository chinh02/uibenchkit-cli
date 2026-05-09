"""
Delete a run from the UIBenchKit API server.
"""
import typer
import requests
from typing import Optional
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Delete a specific run by its ID")


def delete_run(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to delete"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
    force: bool = typer.Option(
        False,
        '--force', '-f',
        help="Skip confirmation prompt"
    ),
):
    """Delete a specific run by its ID."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete run '{run_id}'?")
        if not confirm:
            console.print("[yellow]Deletion cancelled[/]")
            raise typer.Exit(0)
    
    payload = {"run_id": run_id}
    
    with console.status(f"[blue]Deleting run {run_id}..."):
        response = requests.post(
            f"{API_BASE_URL}/delete-run",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    
    console.print(f"[green]✓ {result.get('message', f'Run {run_id} deleted successfully')}[/]")


if __name__ == "__main__":
    app()

