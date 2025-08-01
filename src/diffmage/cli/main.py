import json
import typer
from diffmage.core.models import CommitAnalysis
from rich.table import Table
from rich.panel import Panel
import click

from diffmage.cli.shared import app, console
from diffmage.git.diff_parser import GitDiffParser


@app.command()
def analyze(
    repo_path: str = typer.Option(
        ".", "--repo-path", "-r", help="Path to git repository"
    ),
    output_format: str = typer.Option(
        "summary", "--output", "-o", help="Output format: summary, json, table"
    ),
) -> None:
    """Analyze git changes and extract structured information"""

    try:
        parser = GitDiffParser(repo_path)
        analysis = parser.parse_staged_changes()

        if output_format == "json":
            click.echo(json.dumps(analysis.to_ai_context(), indent=2))
        elif output_format == "table":
            display_table_output(analysis)
        else:
            display_summary_output(analysis)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def display_summary_output(analysis: CommitAnalysis) -> None:
    """Rich summary display of commit analysis"""
    # Header
    console.print(
        Panel(
            f"[bold]{analysis.total_files}[/bold] files changed | "
            f"[green]+{analysis.total_lines_added}[/green]/[red]-{analysis.total_lines_removed}[/red]",
            title="Diffmage Analysis",
        )
    )

    if analysis.files:
        console.print("\n Changed Files:")
        for file_diff in analysis.files[:10]:
            icon = "✨" if file_diff.change_type.value == "added" else "✏️"
            console.print(
                f"  {icon} {file_diff.new_path} ({file_diff.file_type.value})"
            )

        if len(analysis.files) > 10:
            console.print(f"  ... and {len(analysis.files) - 10} more files")


def display_table_output(analysis: CommitAnalysis) -> None:
    """Table format display of commit analysis"""
    table = Table(title="File Changes")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Change", style="yellow")
    table.add_column("Lines +/-", style="green")

    for file_diff in analysis.files:
        table.add_row(
            file_diff.new_path,
            file_diff.file_type.value,
            file_diff.change_type.value,
            f"[green]+{file_diff.lines_added}[/green]/[red]-{file_diff.lines_removed}[/red]",
        )

    console.print(table)


if __name__ == "__main__":
    app()
