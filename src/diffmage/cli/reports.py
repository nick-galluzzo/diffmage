import typer
from diffmage.cli.shared import app, console
from diffmage.evaluation.evaluation_report import EvaluationReport
from diffmage.evaluation.service import EvaluationService


@app.command()
def batch_report(
    from_commit: str = typer.Argument(
        ..., help="Start of git commit range (e.g., 'HEAD~10', 'abc456'). Inclusive."
    ),
    to_commit: str = typer.Option(
        "HEAD",
        help="End of git commit range (e.g., 'HEAD', 'abc123'). Inclusive. Defaults to current HEAD.",
    ),
    model_name: str = typer.Option(
        None, "--model", "-m", help="AI model to use for evaluation"
    ),
    repo_path: str = typer.Option(
        ".", "--repo-path", "-r", help="Path to git repository"
    ),
    export_csv: bool = typer.Option(False, "--csv", "-c", help="Export results to CSV"),
    export_json: bool = typer.Option(
        False, "--json", "-j", help="Export results to JSON"
    ),
) -> None:
    """Generate a report for a batch of commits"""

    service = EvaluationService()

    try:
        reporter = EvaluationReport(service)

        results = reporter.batch_evaluate_commits(
            from_commit,
            to_commit,
            repo_path,
            model_name,
        )

        if export_csv:
            csv_path = reporter.export_csv_report(results["results"])
            console.print(f"[green]CSV report exported to {csv_path}[/green]")

        if export_json:
            json_path = reporter.export_json_report(results["results"])
            console.print(f"[green]JSON report exported to {json_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(1)
