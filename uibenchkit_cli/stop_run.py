"""
Stop a running job on the UIBenchKit API server.
"""
import requests
import typer
import time
from typing import Optional
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Stop a running job")


def stop_run(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to stop"
    ),
    run_evaluation: bool = typer.Option(
        True,
        '--evaluate/--no-evaluate',
        help="Run evaluation on completed instances after stopping"
    ),
    wait: bool = typer.Option(
        True,
        '--wait/--no-wait',
        help="eait for evaluation to complete (if --evaluate)"
    ),
    timeout: int = typer.Option(
        600,
        '--timeout', '-t',
        help="Timeout in seconds for waiting (default: 10 minutes)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """
    Stop a running job and optionally run evaluation on completed instances.
    
    This is useful when you want to stop a long-running job early and
    evaluate only the instances that have completed so far.
    
    Examples:
    
        # Stop and evaluate completed instances
        uibenchkit stop-run design2code_direct_gpt-4o_20251230_003423
        
        # Stop without evaluation
        uibenchkit stop-run design2code_direct_gpt-4o_20251230_003423 --no-evaluate
    """
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {
        "run_id": run_id,
        "run_evaluation": run_evaluation
    }
    
    console.print(f"[blue]Stopping run {run_id}...[/]")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/stop-run",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Run stopped![/]")
    console.print(f"  Completed: [green]{result.get('completed_instances', 0)}[/]")
    console.print(f"  Stopped: [yellow]{result.get('stopped_instances', 0)}[/]")
    console.print(f"  Skipped: [dim]{result.get('skipped_instances', 0)}[/]")
    
    if not result.get('evaluation_started'):
        console.print(f"\n[yellow]Use 'uibenchkit rerun-evaluation {run_id}' to run evaluation later[/]")
        return
    
    if not wait:
        console.print(f"\n[yellow]Evaluation running in background. Use 'uibenchkit poll {run_id}' to check status[/]")
        return
    
    # eait for evaluation to complete
    console.print(f"\n[blue]eaiting for evaluation to complete...[/]")
    
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            console.print(f"[red]Timeout waiting for evaluation[/]")
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
            console.print(f"[green]✓ Evaluation complete![/]")
            
            # Show evaluation results if available
            evaluation = poll_data.get('evaluation', {})
            if evaluation:
                metrics = evaluation.get('metrics', {})
                clip = metrics.get('clip', {})
                code_sim = metrics.get('code_similarity', {})
                
                if isinstance(clip, dict) and 'average' in clip:
                    console.print(f"  CLIP Score (avg): [cyan]{clip['average']:.4f}[/]")
                if isinstance(code_sim, dict) and 'average' in code_sim:
                    console.print(f"  Code Similarity (avg): [cyan]{code_sim['average']:.2f}%[/]")
            
            # Show cost estimate if available
            cost_estimate = poll_data.get('cost_estimate', {})
            if cost_estimate:
                console.print(f"  Total Cost: [cyan]${cost_estimate.get('total_cost_usd', 0):.4f}[/]")
            
            console.print(f"\n[yellow]Use 'uibenchkit get-report {run_id}' for full report[/]")
            return
        
        if status == 'failed':
            console.print(f"[red]Evaluation failed[/]")
            raise typer.Exit(1)
        
        time.sleep(2)


if __name__ == "__main__":
    app()

