"""
Dataset management commands for the UIBenchKit API.
"""
import requests
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Dataset management commands")


def list_datasets(
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """List all available datasets."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    with console.status("[blue]Fetching datasets..."):
        response = requests.get(f"{API_BASE_URL}/datasets", headers=headers)
        verify_response(response)
        result = response.json()
    
    datasets = result.get('datasets', [])
    
    if not datasets:
        console.print("[yellow]No datasets available[/]")
        return
    
    table = Table(title="Available Datasets")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Samples", style="green", justify="right")
    table.add_column("Downloaded", style="yellow", justify="center")
    
    for ds in datasets:
        table.add_row(
            ds.get('name', 'N/A'),
            ds.get('description', 'N/A')[:50] + '...' if len(ds.get('description', '')) > 50 else ds.get('description', 'N/A'),
            str(ds.get('num_samples', 'N/A')),
            '✓' if ds.get('downloaded') else '✗'
        )
    
    console.print(table)


def info(
    dataset_name: str = typer.Argument(
        ...,
        help="Dataset name (design2code, dcgen)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """Get detailed information about a dataset."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    with console.status(f"[blue]Fetching info for {dataset_name}..."):
        response = requests.get(
            f"{API_BASE_URL}/datasets/{dataset_name}",
            headers=headers
        )
        verify_response(response)
        result = response.json()
    
    if not result.get('downloaded'):
        console.print(f"[yellow]Dataset {dataset_name} is not downloaded[/]")
        console.print(f"[dim]{result.get('message', '')}[/]")
        return
    
    info = result.get('info', {})
    
    console.print(f"\n[bold cyan]═══ Dataset: {dataset_name} ═══[/]\n")
    console.print(f"[bold]Name:[/] {info.get('name', 'N/A')}")
    console.print(f"[bold]Description:[/] {info.get('description', 'N/A')}")
    console.print(f"[bold]HuggingFace ID:[/] {info.get('hf_id', 'N/A')}")
    console.print(f"[bold]Total Samples:[/] {info.get('num_samples', 'N/A')}")
    console.print(f"[bold]Local Path:[/] {info.get('local_path', 'N/A')}")
    
    sample_ids = info.get('sample_ids', [])
    if sample_ids:
        preview = sample_ids[:10]
        console.print(f"[bold]Sample IDs:[/] {', '.join(preview)}" + 
                     (f" ... ({len(sample_ids)} total)" if len(sample_ids) > 10 else ""))


def samples(
    dataset_name: str = typer.Argument(
        ...,
        help="Dataset name"
    ),
    limit: Optional[int] = typer.Option(
        10,
        '--limit', '-l',
        help="Maximum samples to show"
    ),
    offset: int = typer.Option(
        0,
        '--offset',
        help="Starting offset"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """List samples from a dataset."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    params = {"offset": offset}
    if limit:
        params["limit"] = limit
    
    with console.status(f"[blue]Fetching samples from {dataset_name}..."):
        response = requests.get(
            f"{API_BASE_URL}/datasets/{dataset_name}/samples",
            headers=headers,
            params=params
        )
        verify_response(response)
        result = response.json()
    
    samples = result.get('samples', [])
    total = result.get('total', 0)
    
    if not samples:
        console.print(f"[yellow]No samples found in {dataset_name}[/]")
        return
    
    table = Table(title=f"Samples from {dataset_name} ({offset+1}-{offset+len(samples)} of {total})")
    table.add_column("ID", style="cyan")
    table.add_column("Image", style="green")
    table.add_column("HTML", style="blue")
    
    for sample in samples:
        table.add_row(
            sample.get('id', 'N/A'),
            '✓' if sample.get('image_path') else '✗',
            '✓' if sample.get('html_path') else '✗'
        )
    
    console.print(table)
    
    if offset + len(samples) < total:
        console.print(f"\n[dim]Use --offset {offset + limit} to see more[/]")


# Register commands
app.command(name="list")(list_datasets)
app.command(name="info")(info)
app.command(name="samples")(samples)


if __name__ == "__main__":
    app()

