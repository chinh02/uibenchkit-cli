"""
Submit benchmarks to the UIBenchKit API server.
"""
import json
import time
import requests
import typer
import sys
from typing import Optional, List
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.console import Console
from uibenchkit_cli.config import API_BASE_URL, Method, MODEL_VERSIONS
from uibenchkit_cli.utils import verify_response
from pathlib import Path

app = typer.Typer(help="Submit benchmarks to the UIBenchKit API")


def process_poll_response(results: dict, all_ids: list[str] = None):
    """Process polling response and categorize instance IDs."""
    running_ids = results.get('running', [])
    completed_ids = results.get('completed', [])
    pending_ids = results.get('pending', [])
    failed_ids = results.get('failed', [])
    return {
        'running': running_ids,
        'completed': completed_ids,
        'pending': pending_ids,
        'failed': failed_ids,
        'status': results.get('status', 'unknown')
    }


def run_progress_task(
    console: Console, 
    task_name: str, 
    total: int, 
    task_func, 
    timeout: Optional[int] = None, 
    *args, 
    **kwargs
):
    """Run a task with a progress bar and a default timeout."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[blue]{task_name}..."),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:>3.1f}%"),
        TimeElapsedColumn(),
        console=console,
    )
    start_time = time.time()
    completed = 0
    exception = None
    with progress:
        task = progress.add_task("", total=total)
        try:
            result = task_func(progress, task, *args, **kwargs)
        except Exception as e:
            exception = e
        finally:
            elapsed_time = time.time() - start_time
            progress.stop()
            if exception:
                console.print(f"[red]Error during task: {str(exception)}[/]")
                raise exception
            final_percentage = progress.tasks[task].completed / progress.tasks[task].total * 100 if progress.tasks[task].total > 0 else 0
            completed = progress.tasks[task].completed
            total = progress.tasks[task].total
            progress.remove_task(task)
            if completed == total and total > 0:
                console.print(f"[green]✓ {task_name} complete![/]")
            elif timeout and elapsed_time > timeout:
                console.print(f"[red]✗ {task_name} timed out after {timeout} seconds. Try re-running submit to continue.[/]")
                sys.exit(1)
            else:
                console.print(f"[yellow]✓ {task_name} completed with {completed}/{total} instances[/]")
    return {
        "result": result,
        "elapsed_time": elapsed_time,
        "final_percentage": final_percentage,
        "completed": completed,
        "total": total,
        "timeout": timeout and elapsed_time > timeout,
    }


def wait_for_completion(
    *, 
    run_id: str, 
    api_key: str, 
    total_instances: int,
    timeout: int,
    console: Console
):
    """Spin a progress bar until all predictions are complete."""
    def task_func(progress, task):
        headers = {"x-api-key": api_key}
        start_time = time.time()
        while True:
            poll_response = requests.get(
                f'{API_BASE_URL}/poll-jobs',
                params={'run_id': run_id},
                headers=headers
            )
            verify_response(poll_response)
            poll_results = process_poll_response(poll_response.json())
            
            completed_count = len(poll_results['completed'])
            failed_count = len(poll_results['failed'])
            progress.update(task, completed=completed_count + failed_count)
            
            if poll_results['status'] in ['completed', 'failed']:
                return poll_results
            
            if (time.time() - start_time) > timeout:
                return poll_results
            
            time.sleep(5)
    
    result = run_progress_task(
        console,
        "Running evaluation", 
        total_instances, 
        task_func,
        timeout=timeout,
    )
    return result.get("result", {})


def submit(
    model: str = typer.Argument(
        ..., 
        help="Model to use (family or specific version, e.g., 'gemini', 'gpt-4o-mini', 'claude-3-opus-20240229')"
    ),
    method: Method = typer.Argument(
        ...,
        help="Generation method: dcgen, direct, latcoder, uicopilot, or layoutcoder"
    ),
    dataset: Optional[str] = typer.Option(
        None,
        '--dataset', '-d',
        help="Dataset to benchmark (design2code, dcgen)"
    ),
    input_dir: Optional[str] = typer.Option(
        None,
        '--input-dir', '-i',
        help="Input directory with PNG images (alternative to dataset)"
    ),
    sample_ids: Optional[str] = typer.Option(
        None,
        '--sample-ids', '-s',
        help="Comma-separated sample IDs to run (e.g., '0,1,2,3')"
    ),
    run_id: Optional[str] = typer.Option(
        None,
        '--run-id', '-r',
        help="Custom run ID (auto-generated if not provided)"
    ),
    output_dir: Optional[str] = typer.Option(
        'results',
        '--output-dir', '-o',
        help="Directory to save report files"
    ),
    wait: bool = typer.Option(
        True,
        '--wait/--no-wait',
        help="Wait for completion before returning"
    ),
    timeout: int = typer.Option(
        1800,
        '--timeout', '-t',
        help="Timeout in seconds for waiting (default: 30 minutes)"
    ),
    gen_report: bool = typer.Option(
        True,
        '--report/--no-report',
        help="Generate report after completion"
    ),
    api_key: Optional[str] = typer.Option(
        None, 
        '--api-key', '-k',
        help="API key (defaults to UIBENCHKIT_API_KEY env var)", 
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """
    Submit a benchmark run to the UIBenchKit API server.
    
    Examples:
    
        # Run DCGen method on design2code dataset with gemini
        uibenchkit submit gemini dcgen --dataset design2code
        
        # Run direct method with specific model version
        uibenchkit submit gpt-4o-mini direct --dataset dcgen --sample-ids 0,1,2
        
        # Run latcoder (block-based) method
        uibenchkit submit claude latcoder --dataset design2code

        # Run uicopilot (bbox-tree + LLM) method
        uibenchkit submit gpt-4o uicopilot --dataset design2code

        # Run layoutcoder method
        uibenchkit submit claude layoutcoder --dataset design2code

        # Run on custom input directory
        uibenchkit submit claude direct --input-dir ./my_images
    """
    console = Console()
    
    # Validate inputs
    if not dataset and not input_dir:
        console.print("[red]Error: Either --dataset or --input-dir must be provided[/]")
        raise typer.Exit(1)
    
    # Parse sample_ids
    sample_id_list = None
    if sample_ids:
        sample_id_list = [s.strip() for s in sample_ids.split(',')]
    
    # Build request payload
    payload = {
        "model": model,
        "method": method.value,
    }
    
    if dataset:
        payload["dataset"] = dataset
    if input_dir:
        payload["input_dir"] = input_dir
    if sample_id_list:
        payload["sample_ids"] = sample_id_list
    if run_id:
        payload["run_id"] = run_id
    
    headers = {"x-api-key": api_key} if api_key else {}
    
    # Submit the run
    console.print(f"[blue]Submitting benchmark run...[/]")
    console.print(f"  Model: [cyan]{model}[/]")
    console.print(f"  Method: [cyan]{method.value}[/]")
    if dataset:
        console.print(f"  Dataset: [cyan]{dataset}[/]")
    if input_dir:
        console.print(f"  Input Dir: [cyan]{input_dir}[/]")
    if sample_id_list:
        console.print(f"  Samples: [cyan]{', '.join(sample_id_list)}[/]")
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/submit',
            json=payload,
            headers=headers
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error submitting run: {e}[/]")
        raise typer.Exit(1)
    
    if not result.get("launched"):
        console.print(f"[yellow]Run not launched: {result.get('message')}[/]")
        console.print(f"[yellow]Run ID: {result.get('run_id')}[/]")
        raise typer.Exit(0)
    
    run_id = result["run_id"]
    console.print(f"[green]✓ Run submitted successfully![/]")
    console.print(f"  Run ID: [cyan]{run_id}[/]")
    console.print(f"  Model: [cyan]{result.get('model')}[/] (family: {result.get('model_family')})")
    
    if not wait:
        console.print(f"\n[yellow]Use 'uibenchkit poll {run_id}' to check status[/]")
        return
    
    # Wait for completion
    console.print(f"\n[blue]Waiting for completion...[/]")
    
    # First poll to get total instances
    poll_response = requests.get(
        f'{API_BASE_URL}/poll-jobs',
        params={'run_id': run_id},
        headers=headers
    )
    verify_response(poll_response)
    poll_data = poll_response.json()
    
    total_instances = (
        len(poll_data.get('running', [])) + 
        len(poll_data.get('completed', [])) + 
        len(poll_data.get('pending', [])) +
        len(poll_data.get('failed', []))
    )
    
    if total_instances == 0:
        total_instances = 1  # At least show some progress
    
    final_status = wait_for_completion(
        run_id=run_id,
        api_key=api_key,
        total_instances=total_instances,
        timeout=timeout,
        console=console
    )
    
    # Show summary
    completed = len(final_status.get('completed', []))
    failed = len(final_status.get('failed', []))
    console.print(f"\n[green]Completed: {completed}[/] | [red]Failed: {failed}[/]")
    
    # Generate report
    if gen_report and final_status.get('status') == 'completed':
        from uibenchkit_cli.get_report import get_report as _get_report
        console.print(f"\n[blue]Generating report...[/]")
        _get_report(
            run_id=run_id,
            api_key=api_key,
            output_dir=output_dir,
            overwrite=False
        )


def run_all(
    model: str = typer.Argument(
        ..., 
        help="Model to use (family or specific version)"
    ),
    dataset: Optional[str] = typer.Option(
        None,
        '--dataset', '-d',
        help="Dataset to benchmark (design2code, dcgen)"
    ),
    input_dir: Optional[str] = typer.Option(
        None,
        '--input-dir', '-i',
        help="Input directory with PNG images"
    ),
    sample_ids: Optional[str] = typer.Option(
        None,
        '--sample-ids', '-s',
        help="Comma-separated sample IDs to run"
    ),
    run_id: Optional[str] = typer.Option(
        None,
        '--run-id', '-r',
        help="Base run ID (auto-generated if not provided)"
    ),
    api_key: Optional[str] = typer.Option(
        None, 
        '--api-key', '-k',
        help="API key", 
        envvar="UIBENCHKIT_API_KEY"
    ),
):
    """
    Run full pipeline (both DCGen and Direct methods).
    
    Example:
        uibenchkit run-all gemini --dataset design2code --sample-ids 0,1,2
    """
    console = Console()
    
    if not dataset and not input_dir:
        console.print("[red]Error: Either --dataset or --input-dir must be provided[/]")
        raise typer.Exit(1)
    
    # Parse sample_ids
    sample_id_list = None
    if sample_ids:
        sample_id_list = [s.strip() for s in sample_ids.split(',')]
    
    payload = {"model": model}
    if dataset:
        payload["dataset"] = dataset
    if input_dir:
        payload["input_dir"] = input_dir
    if sample_id_list:
        payload["sample_ids"] = sample_id_list
    if run_id:
        payload["run_id"] = run_id
    
    headers = {"x-api-key": api_key} if api_key else {}
    
    console.print(f"[blue]Submitting full pipeline (DCGen + Direct)...[/]")
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/run-all',
            json=payload,
            headers=headers
        )
        verify_response(response)
        result = response.json()
    except Exception as e:
        console.print(f"[red]Error submitting run: {e}[/]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ Full pipeline submitted![/]")
    console.print(f"  Model: [cyan]{result.get('model')}[/] (family: {result.get('model_family')})")
    console.print(f"  Dataset: [cyan]{result.get('dataset')}[/]")
    console.print(f"  Run IDs:")
    for rid in result.get('run_ids', []):
        console.print(f"    - [cyan]{rid}[/]")
    
    console.print(f"\n[yellow]Use 'uibenchkit poll <run_id>' to check status[/]")

