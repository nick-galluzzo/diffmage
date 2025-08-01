import typer
from diffmage.cli.shared import app, console
from diffmage.ai.models import get_default_model
from diffmage.git.diff_parser import GitDiffParser
from diffmage.evaluation.llm_evaluator import LLMEvaluator


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
    """Evaluate a commit message"""

    if not model:
        model = get_default_model().name

    if commit_hash:
        parser = GitDiffParser(repo_path)
        analysis, message = parser.parse_specific_commit(commit_hash)
        git_diff = analysis.get_combined_diff()

    else:
        if not message:
            console.print("[red]Error: Commit message or commit hash is required[/red]")
            raise typer.Exit(1)

        parser = GitDiffParser(repo_path)
        analysis = parser.parse_staged_changes()
        git_diff = analysis.get_combined_diff()

    evaluator = LLMEvaluator(model_name=model)
    result = evaluator.evaluate_commit_message(message, git_diff)

    console.print(f"[green]Commit message:[/green] {result.to_dict()}")
