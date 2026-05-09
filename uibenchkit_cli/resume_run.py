"""
Resume an interrupted/stopped run on the UIBenchKit API server.
"""
import requests
import typer
import time
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Resume an interrupted run")


def resume_run(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to resume"
    ),
    wait: bool = typer.Option(
        True,
        '--wait/--no-wait',
        help="eait for run to complete"
    ),
    timeout: int = typer.Option(
        7200,
        '--timeout', '-t',
        help="Timeout in seconds when waiting (default: 2 hours)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """
    Resume an interrupted or stopped run.
    
    This will continue processing any pending instances that were not
    completed before the run was interrupted.
    
    Examples:
    
        # Resume a stopped run
        uibenchkit resume-run dcgen_dcgen_gemini-2-0-flash_20251231_010352
        
        # Resume without waiting for completion
        uibenchkit resume-run my_run_id --no-wait
    """
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {"run_id": run_id}
    
    console.print(f"[blue]Resuming run {run_id}...[/]")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/resume-run",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Resume started![/]")
    console.print(f"  Run ID: [cyan]{run_id}[/]")
    console.print(f"  Pending instances: [cyan]{result.get('total_pending', 0)}[/]")
    
    if not wait:
        console.print(f"\n[yellow]Use 'uibenchkit poll {run_id}' to check status[/]")
        return
    
    # eait for run to complete
    console.print(f"\n[blue]eaiting for run to complete...[/]")
    
    start_time = time.time()
    last_completed = 0
    
    while True:
        if (time.time() - start_time) > timeout:
            console.print(f"[red]Timeout waiting for run to complete[/]")
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
        completed = len(poll_data.get('completed', []))
        running = len(poll_data.get('running', []))
        pending = len(poll_data.get('pending', []))
        failed = len(poll_data.get('failed', []))
        
        # Show progress if new instances completed
        if completed > last_completed:
            console.print(f"  Progress: [green]{completed}[/] completed, [yellow]{running}[/] running, [blue]{pending}[/] pending, [red]{failed}[/] failed")
            last_completed = completed
        
        if status == 'completed':
            console.print(f"\n[green]✓ Run completed![/]")
            
            # Show final status
            table = Table(title="Run Results")
            table.add_column("Status", style="cyan")
            table.add_column("Count", style="magenta")
            
            table.add_row("Completed", str(completed))
            table.add_row("Failed", str(failed))
            
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
            console.print(f"[red]Run failed: {poll_data.get('error', 'Unknown error')}[/]")
            raise typer.Exit(1)
        
        time.sleep(10)


if __name__ == "__main__":
    app()

