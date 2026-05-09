"""
Health check for the UIBenchKit API server.
"""
import requests
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Check API server health")


def health(
    show_models: bool = typer.Option(
        False,
        '--models', '-m',
        help="Show all supported model versions"
    ),
):
    """Check if the UIBenchKit API server is healthy."""
    console = Console()
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        verify_response(response)
        result = response.json()
    except requests.exceptions.ConnectionError:
        console.print(f"[red]✗ Cannot connect to API server at {API_BASE_URL}[/]")
        console.print("[dim]Make sure the server is running[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/]")
        raise typer.Exit(1)
    
    status = result.get('status', 'unknown')
    if status == 'healthy':
        console.print(f"[green]✓ API server is healthy[/]")
    else:
        console.print(f"[yellow]⚠ API server status: {status}[/]")
    
    console.print(f"\n[bold]Server Info:[/]")
    console.print(f"  URL: {API_BASE_URL}")
    console.print(f"  Version: {result.get('version', 'N/A')}")
    console.print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
    
    console.print(f"\n[bold]Supported:[/]")
    console.print(f"  Datasets: {', '.join(result.get('supported_datasets', []))}")
    console.print(f"  Model Families: {', '.join(result.get('supported_model_families', []))}")
    console.print(f"  Methods: {', '.join(result.get('supported_methods', []))}")
    
    if show_models:
        model_versions = result.get('supported_model_versions', {})
        if model_versions:
            console.print(f"\n[bold]Supported Model Versions:[/]")
            
            for family, config in model_versions.items():
                default = config.get('default', 'N/A')
                versions = config.get('versions', [])
                console.print(f"\n  [cyan]{family}[/] (default: {default})")
                for v in versions:
                    marker = "[green]●[/]" if v == default else "[dim]○[/]"
                    console.print(f"    {marker} {v}")


if __name__ == "__main__":
    app()

