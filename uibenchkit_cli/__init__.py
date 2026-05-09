import typer

app = typer.Typer(
    help="UIBenchKit CLI - Command line interface for the UIBenchKit benchmarking API",
    no_args_is_help=True
)

from . import (
    gen_api_key,
    get_report,
    list_runs,
    submit,
    verify_api_key,
    delete_run,
    get_quotas,
    poll,
    datasets,
    health,
    rerun_evaluation,
    stop_run,
    retry_failed,
    resume_run,
)

# Main commands
app.command(name="submit")(submit.submit)
app.command(name="run-all")(submit.run_all)
app.command(name="poll")(poll.poll)
app.command(name="list-runs")(list_runs.list_runs)
app.command(name="get-report")(get_report.get_report)
app.command(name="delete-run")(delete_run.delete_run)
app.command(name="rerun-evaluation")(rerun_evaluation.rerun_evaluation)
app.command(name="stop-run")(stop_run.stop_run)
app.command(name="retry-failed")(retry_failed.retry_failed)
app.command(name="resume-run")(resume_run.resume_run)

# Utility commands
app.command(name="health")(health.health)
app.command(name="get-quotas")(get_quotas.get_quotas)
app.command(name="verify-api-key")(verify_api_key.verify)
app.command(name="gen-api-key")(gen_api_key.gen_api_key)

# Dataset subcommands
app.add_typer(datasets.app, name="datasets", help="Dataset management commands")


def main():
    """Run the UIBenchKit CLI application"""
    app()
