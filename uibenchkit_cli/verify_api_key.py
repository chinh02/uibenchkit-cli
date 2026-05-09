"""Verify API key with the UIBenchKit API server."""
import requests
import typer
from typing import Optional
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Verify API key")


def verify(
    api_key: Optional[str] = typer.Option(
        None, 
        '--api-key', '-k',
        help="API key to verify", 
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """Verify that your API key is valid."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/verify-api-key",
            headers=headers
        )
        verify_response(response)
        result = response.json()
        console.print(f"[green]✓ {result.get('message', 'API key is valid')}[/]")
        if result.get('email'):
            console.print(f"  Email: {result['email']}")
    except requests.RequestException as e:
        console.print(f"[red]✗ API key verification failed: {e}[/]")
        raise typer.Exit(1)

