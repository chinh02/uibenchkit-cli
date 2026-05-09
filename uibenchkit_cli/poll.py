"""
Poll job status from the UIBenchKit API server.
"""
import requests
import typer
import time
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Poll job status")


def poll(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to poll"
    ),
    watch: bool = typer.Option(
        False,
        '--watch', '-w',
        help="Continuously watch status until completion"
    ),
    interval: int = typer.Option(
        5,
        '--interval', '-i',
        help="Polling interval in seconds (for --watch)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """Poll the status of a run."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    
    def fetch_status():
        response = requests.get(
            f"{API_BASE_URL}/poll-jobs",
            params={"run_id": run_id},
            headers=headers
        )
        verify_response(response)
        return response.json()
    
    def display_status(data: dict):
        status = data.get('status', 'unknown')
        status_color = {
            'completed': 'green',
            'running': 'yellow',
            'pending': 'blue',
            'failed': 'red'
        }.get(status, 'white')
        
        console.print(f"\n[bold]Run:[/] [cyan]{run_id}[/]")
        console.print(f"[bold]Status:[/] [{status_color}]{status}[/]")
        console.print(f"[bold]Model:[/] {data.get('model', 'N/A')}")
        console.print(f"[bold]Method:[/] {data.get('method', 'N/A')}")
        console.print(f"[bold]Dataset:[/] {data.get('dataset', 'N/A') or 'custom'}")
        
        # Instance counts
        running = len(data.get('running', []))
        completed = len(data.get('completed', []))
        pending = len(data.get('pending', []))
        failed = len(data.get('failed', []))
        total = running + completed + pending + failed
        
        console.print(f"\n[bold]Progress:[/]")
        console.print(f"  [green]Completed:[/] {completed}/{total}")
        console.print(f"  [yellow]Running:[/] {running}")
        console.print(f"  [blue]Pending:[/] {pending}")
        console.print(f"  [red]Failed:[/] {failed}")
        
        # Show evaluation if available
        evaluation = data.get('evaluation')
        if evaluation:
            console.print(f"\n[bold]Evaluation:[/]")
            metrics = evaluation.get('metrics', {})
            
            clip = metrics.get('clip', {})
            if isinstance(clip, dict) and 'average' in clip:
                console.print(f"  CLIP Score (avg): [green]{clip['average']:.4f}[/]")
            
            code_sim = metrics.get('code_similarity', {})
            if isinstance(code_sim, dict) and 'average' in code_sim:
                console.print(f"  Code Similarity (avg): [green]{code_sim['average']:.2f}%[/]")
            
            # Show fine-grained metrics if available
            fine_grained = metrics.get('fine_grained', {})
            if fine_grained:
                console.print(f"\n[bold]Fine-Grained Visual Metrics:[/]")
                
                block_match = fine_grained.get('block_match', {})
                if isinstance(block_match, dict) and 'average' in block_match:
                    console.print(f"  Block-Match (avg): [green]{block_match['average']:.4f}[/]")
                
                text = fine_grained.get('text', {})
                if isinstance(text, dict) and 'average' in text:
                    console.print(f"  Text (avg): [green]{text['average']:.4f}[/]")
                
                position = fine_grained.get('position', {})
                if isinstance(position, dict) and 'average' in position:
                    console.print(f"  Position (avg): [green]{position['average']:.4f}[/]")
                
                color = fine_grained.get('color', {})
                if isinstance(color, dict) and 'average' in color:
                    console.print(f"  Color (avg): [green]{color['average']:.4f}[/]")
                
                fg_clip = fine_grained.get('clip', {})
                if isinstance(fg_clip, dict) and 'average' in fg_clip:
                    console.print(f"  CLIP (fine-grained, avg): [green]{fg_clip['average']:.4f}[/]")
                
                overall = fine_grained.get('overall', {})
                if isinstance(overall, dict) and 'average' in overall:
                    console.print(f"  Overall (avg): [bold green]{overall['average']:.4f}[/]")
        
        # Show cost estimate if available
        cost_estimate = data.get('cost_estimate')
        if cost_estimate:
            console.print(f"\n[bold]Cost Estimate:[/]")
            console.print(f"  Total Tokens: [cyan]{cost_estimate.get('total_tokens', 0):,}[/]")
            console.print(f"  Total Cost: [green]${cost_estimate.get('total_cost_usd', 0):.4f}[/]")
        
        return status
    
    if not watch:
        # Single poll
        with console.status(f"[blue]Polling status for {run_id}..."):
            data = fetch_status()
        display_status(data)
    else:
        # Continuous watch
        console.print(f"[blue]eatching run {run_id}... (Ctrl+C to stop)[/]")
        try:
            while True:
                console.clear()
                data = fetch_status()
                status = display_status(data)
                
                if status in ['completed', 'failed']:
                    console.print(f"\n[{'green' if status == 'completed' else 'red'}]Run {status}![/]")
                    break
                
                console.print(f"\n[dim]Refreshing in {interval}s...[/]")
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]eatch stopped[/]")


if __name__ == "__main__":
    app()

