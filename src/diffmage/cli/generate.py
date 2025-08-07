import typer
from rich.table import Table
from diffmage.ai.models import SupportedModels, get_default_model, get_model_by_name
from diffmage.cli.shared import app, console
from diffmage.generation.service import GenerationService
from diffmage.generation.models import GenerationRequest


@app.command()
def generate(
    model: str = typer.Option(
        get_default_model().name, "--model", "-m", help="AI model to use for generation"
    ),
    list_models: bool = typer.Option(
        False, "--list-models", help="List all available models"
    ),
    repo_path: str = typer.Option(".", "--repo", "-r"),
    why_context: str = typer.Option(
        None, "--context", "-c", help="Context to use to improve the WHY generation"
    ),
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

    service = GenerationService(model_name=model_config.name)
    request = GenerationRequest(repo_path=repo_path)

    result = service.generate_commit_message(request, why_context)

    console.print(f"[green]Commit message:[/green] {result.message}")


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
