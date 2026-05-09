"""
Re-run evaluation for a completed run on the UIBenchKit API server.
"""
import requests
import typer
import time
from typing import Optional
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Re-run evaluation for a completed run")


def rerun_evaluation(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to re-evaluate"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
    wait: bool = typer.Option(
        True,
        '--wait/--no-wait',
        help="eait for evaluation to complete"
    ),
    timeout: int = typer.Option(
        600,
        '--timeout', '-t',
        help="Timeout in seconds for waiting (default: 10 minutes)"
    ),
):
    """
    Re-run evaluation for a completed run.
    
    This is useful when the initial evaluation timed out or failed,
    but the generation was successful.
    
    Examples:
    
        uibenchkit rerun-evaluation design2code_direct_gpt-4o_20251230_003423
    """
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {"run_id": run_id}
    
    console.print(f"[blue]Re-running evaluation for {run_id}...[/]")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/rerun-evaluation",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Evaluation started![/]")
    console.print(f"  Run ID: [cyan]{run_id}[/]")
    console.print(f"  Completed Instances: [cyan]{result.get('completed_instances', 'N/A')}[/]")
    
    if not wait:
        console.print(f"\n[yellow]Use 'uibenchkit poll {run_id}' to check status[/]")
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

