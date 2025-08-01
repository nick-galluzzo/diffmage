import typer
from diffmage.cli.shared import app, console
from diffmage.ai.models import get_default_model
from diffmage.evaluation.display import EvaluationDisplayFormatter
from diffmage.evaluation.service import EvaluationService


@app.command()
def evaluate(
    message: str = typer.Argument(None, help="The commit message to evaluate"),
    commit_hash: str = typer.Option(
        None, "--commit", "-c", help="Evaluate specific commit (ie: HEAD, 0deda3c)"
    ),
    model: str = typer.Option(
        str, "--model", "-m", help="AI model to use for evaluation"
    ),
    repo_path: str = typer.Option(".", "--repo", "-r"),
) -> None:
    """Evaluate a commit message and display the results to the console"""

    if not model:
        model = get_default_model().name

    if commit_hash:
        service = EvaluationService(model_name=model)
        result, message = service.evaluate_commit(commit_hash, repo_path)

    else:
        if not message:
            console.print("[red]Error: Commit message or commit hash is required[/red]")
            raise typer.Exit(1)

        service = EvaluationService(model_name=model)
        result, message = service.evaluate_staged_changes(message, repo_path)

    formatter = EvaluationDisplayFormatter(console)
    formatter.display_evaluation_results(result, message)
