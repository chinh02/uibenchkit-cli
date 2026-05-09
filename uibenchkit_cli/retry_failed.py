"""
Retry failed instances in a run on the UIBenchKit API server.
"""
import requests
import typer
import time
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Retry failed instances in a run")


def retry_failed(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to retry failed instances for"
    ),
    max_retries: int = typer.Option(
        3,
        '--max-retries', '-m',
        help="Maximum retry attempts per instance"
    ),
    wait: bool = typer.Option(
        True,
        '--wait/--no-wait',
        help="eait for retry to complete"
    ),
    timeout: int = typer.Option(
        1800,
        '--timeout', '-t',
        help="Timeout in seconds when waiting (default: 30 minutes)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """
    Retry failed instances in a run.
    
    This will re-attempt generation for instances that failed due to temporary
    errors (network issues, API rate limits, etc.) while keeping completed instances.
    
    Examples:
    
        # Retry failed instances with default settings (max 3 retries)
        uibenchkit retry-failed design2code_direct_gpt-4o_20251230_003423
        
        # Retry with custom max retries
        uibenchkit retry-failed my_run_id --max-retries 5
        
        # Retry without waiting for completion
        uibenchkit retry-failed my_run_id --no-wait
    """
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {
        "run_id": run_id,
        "max_retries": max_retries
    }
    
    console.print(f"[blue]Retrying failed instances for {run_id}...[/]")
    console.print(f"  Max retries per instance: [cyan]{max_retries}[/]")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/retry-failed",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Retry started![/]")
    console.print(f"  Run ID: [cyan]{run_id}[/]")
    console.print(f"  Retrying instances: [cyan]{', '.join(result.get('failed_instances', []))}[/]")
    console.print(f"  Total failed instances: [cyan]{len(result.get('failed_instances', []))}[/]")
    
    if not wait:
        console.print(f"\n[yellow]Use 'uibenchkit poll {run_id}' to check status[/]")
        return
    
    # eait for retry to complete
    console.print(f"\n[blue]eaiting for retry to complete...[/]")
    
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            console.print(f"[red]Timeout waiting for retry[/]")
            console.print(f"[yellow]Use 'uibenchkit poll {run_id}' to check status[/]")
            raise typer.Exit(1)
        
        poll_response = requests.get(
            f"{API_BASE_URL}/poll-jobs",
            params={"run_id": run_id},
            headers=headers
        )
        verify_response(poll_response)
        poll_data = poll_response.json()
        
        status = poll_data.get('status', 'unknown')
        
        if status == 'completed':
            console.print(f"[green]✓ Retry completed![/]")
            
            # Show final status
            completed = len(poll_data.get('completed', []))
            failed = len(poll_data.get('failed', []))
            
            table = Table(title="Retry Results")
            table.add_column("Status", style="cyan")
            table.add_column("Count", style="magenta")
            
            table.add_row("Completed", str(completed))
            table.add_row("Still Failed", str(failed))
            
            console.print(table)
            
            # Show evaluation results if available
            evaluation = poll_data.get('evaluation', {})
            if evaluation:
                metrics = evaluation.get('metrics', {})
                
                if 'code_similarity' in metrics:
                    console.print(f"  Code Similarity (avg): [cyan]{metrics['code_similarity']['average']:.2f}%[/]")
                
                if 'clip' in metrics:
                    console.print(f"  CLIP Score (avg): [cyan]{metrics['clip']['average']:.4f}[/]")
            
            # Show cost estimate if available
            cost_estimate = poll_data.get('cost_estimate', {})
            if cost_estimate:
                console.print(f"  Total Cost: [cyan]${cost_estimate.get('total_cost_usd', 0):.4f}[/]")
            
            console.print(f"\n[yellow]Use 'uibenchkit get-report {run_id}' for full report[/]")
            return
        
        if status == 'failed':
            console.print(f"[red]Retry failed[/]")
            raise typer.Exit(1)
        
        # Show progress
        completed = len(poll_data.get('completed', []))
        running = len(poll_data.get('running', []))
        pending = len(poll_data.get('pending', []))
        failed = len(poll_data.get('failed', []))
        
        console.print(f"  Status: [yellow]{status}[/] | Completed: [green]{completed}[/] | Running: [yellow]{running}[/] | Pending: [blue]{pending}[/] | Failed: [red]{failed}[/]", end="\r")
        
        time.sleep(5)


if __name__ == "__main__":
    app()

