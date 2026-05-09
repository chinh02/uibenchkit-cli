"""Generate a new API key for the UIBenchKit API."""
import requests
import typer
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Generate a new API key")


def gen_api_key(
    email: str = typer.Argument(
        ..., 
        help="Email address to associate with the API key"
    )
):
    """
    Generate a new API key for accessing the UIBenchKit API.
    
    The API key will be auto-verified for development purposes.
    """
    console = Console()
    payload = {'email': email}
    
    try:
        response = requests.post(f'{API_BASE_URL}/gen-api-key', json=payload)
        verify_response(response)
        result = response.json()
        
        api_key = result.get('api_key')
        message = result.get('message', 'API key generated')
        
        console.print(f"[green]✓ {message}[/]")
        console.print(f"\n[bold]Your API Key:[/]")
        console.print(f"  [cyan]{api_key}[/]")
        console.print(f"\n[bold]To save your API key:[/]")
        console.print(f"  [dim]# Add to your shell profile (.bashrc, .zshrc, etc.):[/]")
        console.print(f"  export UIBENCHKIT_API_KEY={api_key}")
        console.print(f"\n  [dim]# Or on Windows PowerShell:[/]")
        console.print(f"  $env:UIBENCHKIT_API_KEY = \"{api_key}\"")
    except requests.RequestException as e:
        console.print(f"[red]✗ Failed to generate API key: {e}[/]")
        raise typer.Exit(1)

