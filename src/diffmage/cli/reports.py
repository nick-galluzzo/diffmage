import typer
from diffmage.cli.shared import app, console
from diffmage.evaluation.evaluation_report import EvaluationReport
from diffmage.evaluation.service import EvaluationService
from diffmage.evaluation.benchmarks import EvaluationBenchmarks
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator


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


@app.command()
def benchmark_stability(
    message: str = typer.Argument(..., help="Commit message to evaluate"),
    commit_hash: str = typer.Option(None, "--commit", "-c", help="Use commit's diff"),
    runs: int = typer.Option(2, "--runs", "-n", help="Number of runs to perform"),
    model_name: str = typer.Option(
        None, "--model", "-m", help="AI model to use for evaluation"
    ),
    repo_path: str = typer.Option(
        ".", "--repo-path", "-r", help="Path to git repository"
    ),
) -> None:
    """Evaluate the stability of a commit message"""

    try:
        from diffmage.git.diff_parser import GitDiffParser

        parser = GitDiffParser(repo_path)
        if commit_hash:
            analysis, diff = parser.parse_specific_commit(commit_hash)
        else:
            analysis = parser.parse_staged_changes()
            diff = analysis.get_combined_diff()

        evaluator = CommitMessageEvaluator(model_name)
        benchmarks = EvaluationBenchmarks(evaluator)

        result = benchmarks.stability_test(message, diff, runs, variance_threshold=0.2)

        if result["is_stable"]:
            console.print(
                f"\n[green]✅ Evaluator is STABLE (max variance: {result['max_variance']:.2f})[/green]"
            )
        else:
            console.print(
                f"\n[red]⚠️ Evaluator is UNSTABLE (max variance: {result['max_variance']:.2f})[/red]"
            )

    except Exception as e:
        console.print(f"[red]Error evaluating stability: {e}[/red]")
        raise typer.Exit(1)
