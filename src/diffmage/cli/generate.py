import typer
from rich.table import Table
from diffmage.core.models import CommitAnalysis
from diffmage.ai.models import SupportedModels, get_default_model, get_model_by_name
from diffmage.cli.shared import app, console
from diffmage.ai.client import AIClient
from diffmage.git.diff_parser import GitDiffParser
from diffmage.evaluation.llm_evaluator import LLMEvaluator


@app.command()
def generate(
    model: str = typer.Option(
        get_default_model().name, "--model", "-m", help="AI model to use for generation"
    ),
    list_models: bool = typer.Option(
        False, "--list-models", help="List all available models"
    ),
    repo_path: str = typer.Option(".", "--repo", "-r"),
) -> None:
    """Generate commit message from staged changes"""

    if list_models:
        _display_available_models()
        return

    # Validate model exists
    try:
        model_config = get_model_by_name(model)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("Use --list-models to see available models")
        raise typer.Exit(1)

    # Parse changes and generate commit message
    client = AIClient(model_name=model_config.name)
    parser = GitDiffParser(repo_path=repo_path)
    analysis: CommitAnalysis = parser.parse_staged_changes()
    commit_message = client.generate_commit_message(analysis)

    # Evaluate commit message
    git_diff = analysis.get_combined_diff()
    evaluator = LLMEvaluator(model_name=model_config.name)
    evaluation_result = evaluator.evaluate_commit_message(commit_message, git_diff)

    console.print(f"[green]Commit message:[/green] {commit_message}")
    console.print(f"[cyan]Evaluation result:[/cyan] {evaluation_result.to_dict()}")


def _display_available_models() -> None:
    """Display all available models"""

    table = Table(title="Available AI Models")
    table.add_column("Name", style="bold")
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Description")

    for model_enum in SupportedModels:
        model_config = model_enum.value
        table.add_row(
            model_config.display_name, model_config.name, model_config.description
        )

    console.print(table)
