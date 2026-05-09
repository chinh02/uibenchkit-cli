"""
Get evaluation report for a run from the UIBenchKit API server.
"""
import json
import os
import requests
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from uibenchkit_cli.config import API_BASE_URL
from uibenchkit_cli.utils import verify_response

app = typer.Typer(help="Get the evaluation report for a specific run")


def safe_save_json(data: dict, file_path: Path, overwrite: bool = False):
    """Save JSON data to file, handling existing files."""
    if file_path.exists() and not overwrite:
        ext = 1
        base_stem = file_path.stem
        while (file_path.parent / f"{base_stem}-{ext}.json").exists():
            ext += 1
        file_path = file_path.parent / f"{base_stem}-{ext}.json"
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path


def format_report(report: dict) -> str:
    """Format report for display."""
    lines = []
    lines.append(f"Run ID: {report.get('run_id', 'N/A')}")
    lines.append(f"Model: {report.get('model', 'N/A')}")
    lines.append(f"Method: {report.get('method', 'N/A')}")
    lines.append(f"Dataset: {report.get('dataset', 'N/A') or 'custom'}")
    lines.append(f"Total Instances: {report.get('total_instances', 'N/A')}")
    lines.append(f"Completed: {report.get('completed_instances', 'N/A')}")
    lines.append(f"Failed: {report.get('failed_instances', 'N/A')}")
    
    # Token usage and cost
    token_usage = report.get('token_usage', {})
    cost_estimate = report.get('cost_estimate', {})
    
    if token_usage:
        lines.append("")
        lines.append("Token Usage:")
        lines.append(f"  Input Tokens: {token_usage.get('total_prompt_tokens', 0):,}")
        lines.append(f"  Output Tokens: {token_usage.get('total_response_tokens', 0):,}")
        lines.append(f"  Total Tokens: {token_usage.get('total_tokens', 0):,}")
        lines.append(f"  API Calls: {token_usage.get('call_count', 0)}")
    
    if cost_estimate:
        lines.append("")
        lines.append("Cost Estimate:")
        lines.append(f"  Input Cost: ${cost_estimate.get('input_cost_usd', 0):.4f}")
        lines.append(f"  Output Cost: ${cost_estimate.get('output_cost_usd', 0):.4f}")
        lines.append(f"  Total Cost: ${cost_estimate.get('total_cost_usd', 0):.4f}")
        if report.get('total_instances'):
            cost_per_instance = cost_estimate.get('total_cost_usd', 0) / max(report.get('total_instances', 1), 1)
            lines.append(f"  Cost/Instance: ${cost_per_instance:.6f}")
    
    # Evaluation metrics
    evaluation = report.get('evaluation', {})
    if evaluation:
        metrics = evaluation.get('metrics', {})
        
        lines.append("")
        # CLIP score
        clip = metrics.get('clip', {})
        if isinstance(clip, dict) and 'average' in clip:
            lines.append(f"CLIP Score (avg): {clip['average']:.4f}")
        elif isinstance(clip, dict) and 'error' in clip:
            lines.append(f"CLIP Score: {clip['error']}")
        
        # Code similarity
        code_sim = metrics.get('code_similarity', {})
        if isinstance(code_sim, dict) and 'average' in code_sim:
            lines.append(f"Code Similarity (avg): {code_sim['average']:.2f}%")
    
    lines.append("")
    lines.append(f"Created: {report.get('created_at', 'N/A')}")
    lines.append(f"Completed: {report.get('completed_at', 'N/A')}")
    
    return "\n".join(lines)


def get_report(
    run_id: str = typer.Argument(
        ...,
        help="Run ID to get report for"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        '--api-key', '-k',
        help="API key",
        envvar="UIBENCHKIT_API_KEY"
    ),
    overwrite: bool = typer.Option(
        False,
        '--overwrite',
        help="Overwrite existing report file"
    ),
    output_dir: Optional[str] = typer.Option(
        'results',
        '--output-dir', '-o',
        help="Cirectory to save report files"
    ),
    save: bool = typer.Option(
        True,
        '--save/--no-save',
        help="Save report to file"
    ),
):
    """Get evaluation report for a run."""
    console = Console()
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {"run_id": run_id}
    
    with console.status(f"[blue]Fetching report for run {run_id}..."):
        response = requests.post(
            f"{API_BASE_URL}/get-report",
            headers=headers,
            json=payload
        )
        verify_response(response)
        result = response.json()
    
    report = result.get('report', {})
    
    if not report:
        console.print(f"[red]No report found for run {run_id}[/]")
        return
    
    # Cisplay report
    console.print(f"\n[bold cyan]═══ Report for {run_id} ═══[/]\n")
    console.print(format_report(report))
    
    # Show evaluation metrics in a table
    evaluation = report.get('evaluation', {})
    if evaluation:
        metrics = evaluation.get('metrics', {})
        
        if metrics:
            console.print(f"\n[bold]Evaluation Metrics:[/]")
            
            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Average", style="green", justify="right")
            table.add_column("Samples", style="dim", justify="right")
            
            clip = metrics.get('clip', {})
            if isinstance(clip, dict) and 'average' in clip:
                table.add_row(
                    "CLIP Score",
                    f"{clip['average']:.4f}",
                    str(len(clip.get('scores', {})))
                )
            
            code_sim = metrics.get('code_similarity', {})
            if isinstance(code_sim, dict) and 'average' in code_sim:
                table.add_row(
                    "Code Similarity",
                    f"{code_sim['average']:.2f}%",
                    str(len(code_sim.get('scores', {})))
                )
            
            console.print(table)
            
            # Show fine-grained metrics if available
            fine_grained = metrics.get('fine_grained', {})
            if fine_grained:
                console.print(f"\n[bold]Fine-Grained Visual Metrics:[/]")
                
                fg_table = Table()
                fg_table.add_column("Metric", style="cyan")
                fg_table.add_column("Average", style="green", justify="right")
                fg_table.add_column("Samples", style="dim", justify="right")
                
                metric_names = [
                    ('block_match', 'Block-Match'),
                    ('text', 'Text'),
                    ('position', 'Position'),
                    ('color', 'Color'),
                    ('clip', 'CLIP'),
                    ('overall', 'Overall')
                ]
                
                for key, label in metric_names:
                    metric_data = fine_grained.get(key, {})
                    if isinstance(metric_data, dict) and 'average' in metric_data:
                        fg_table.add_row(
                            label,
                            f"{metric_data['average']:.4f}",
                            str(len(metric_data.get('scores', {})))
                        )
                
                console.print(fg_table)
    
    # Show cost summary in a table
    cost_estimate = report.get('cost_estimate', {})
    if cost_estimate:
        console.print(f"\n[bold]Cost Summary:[/]")
        
        cost_table = Table()
        cost_table.add_column("Item", style="cyan")
        cost_table.add_column("Value", style="green", justify="right")
        
        cost_table.add_row("Model", cost_estimate.get('model', 'N/A'))
        cost_table.add_row("Input Tokens", f"{cost_estimate.get('input_tokens', 0):,}")
        cost_table.add_row("Output Tokens", f"{cost_estimate.get('output_tokens', 0):,}")
        cost_table.add_row("Total Tokens", f"{cost_estimate.get('total_tokens', 0):,}")
        cost_table.add_row("API Calls", str(cost_estimate.get('call_count', 0)))
        cost_table.add_row("Input Cost", f"${cost_estimate.get('input_cost_usd', 0):.4f}")
        cost_table.add_row("Output Cost", f"${cost_estimate.get('output_cost_usd', 0):.4f}")
        cost_table.add_row("Total Cost", f"[bold]${cost_estimate.get('total_cost_usd', 0):.4f}[/]")
        
        console.print(cost_table)
    
    # Save report
    if save and output_dir:
        output_path = Path(output_dir)
        file_path = output_path / f"{run_id}_report.json"
        saved_path = safe_save_json(report, file_path, overwrite)
        console.print(f"\n[green]Report saved to: {saved_path}[/]")


if __name__ == "__main__":
    app()

