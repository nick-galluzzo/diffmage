import typer
from rich.console import Console
from rich.table import Table
from diffmage.core.models import CommitAnalysis
from diffmage.ai.models import SupportedModels, get_default_model, get_model_by_name
from diffmage.cli.shared import app
from diffmage.ai.client import AIClient
from diffmage.git.diff_parser import GitDiffParser

console = Console()


@app.command()
def generate(
    model: str = typer.Option(
        get_default_model().name, "--model", "-m", help="AI model to use for generation"
    ),
    list_models: bool = typer.Option(
        False, "--list-models", help="List all available models"
    ),
    repo_path: str = typer.Option(".", "--repo", "-r"),
):
    """Generate commit message from staged changes"""

    if list_models:
        display_available_models()
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

    console.print(f"[green]Commit message:[/green] {commit_message}")


def display_available_models():
    """Display all available models"""

    table = Table(title="Available AI Models")
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for model_enum in SupportedModels:
        model_config = model_enum.value
        table.add_row(model_config.display_name, model_config.description)

    console.print(table)
