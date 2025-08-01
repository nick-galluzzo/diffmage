from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import SIMPLE

from .models import EvaluationResult, QualityRater


class EvaluationDisplayFormatter:
    def __init__(self, console: Console) -> None:
        self.console = console

    def display_evaluation_results(
        self, result: EvaluationResult, message: str
    ) -> None:
        """Display evaluation quality overview to the console

        Args:
          result: EvaluationResult object containing evaluation results
          message: Commit message to display
        """

        overall_rating: str = result.quality_level

        # Display components
        self._display_commit_message(message)
        self._display_quality_overview(result, overall_rating)
        self._display_score_breakdown(result)
        self._display_analysis(result)
        self._display_metadata(result)

    def _display_commit_message(self, message: str) -> None:
        """Display the commit message panel"""
        panel = Panel(
            Text(message, style="white"),
            title="[bold blue]Commit Message[/bold blue]",
            border_style="blue",
            padding=(0, 1),
        )
        self.console.print(panel)

    def _display_quality_overview(self, result: EvaluationResult, rating: str) -> None:
        """Display the quality overview panel"""
        quality_text = Text()
        quality_text.append("Overall quality: ", style="bold")
        quality_text.append(
            rating, style=f"bold {QualityRater.get_rating_color(result.overall_score)}"
        )
        quality_text.append(
            f" ({result.overall_score:.2f}/5)",
            style=QualityRater.get_rating_color(result.overall_score),
        )

        self.console.print(f"\n{quality_text}\n")

    def _display_score_breakdown(self, result: EvaluationResult) -> None:
        """Display the detailed score breakdown table"""
        table = Table(show_header=True, header_style="bold cyan", box=SIMPLE)
        table.add_column("Score", justify="right", width=8)
        table.add_column("Rating", width=12)
        table.add_column("Reasoning", style="dim")

        # WHAT score row
        what_color = QualityRater.get_rating_color(result.what_score)
        what_rating = QualityRater.get_quality_level(result.what_score)
        table.add_row(
            "WHAT",
            f"[{what_color}]{result.what_score:.2f}[/{what_color}]",
            f"[{what_color}]{what_rating}[/{what_color}]",
        )

        # WHY score row
        why_color = QualityRater.get_rating_color(result.why_score)
        why_rating = QualityRater.get_quality_level(result.why_score)
        table.add_row(
            "WHY",
            f"[{why_color}]{result.why_score:.2f}[/{why_color}]",
            f"[{why_color}]{why_rating}[/{why_color}]",
        )

        self.console.print(table)

    def _display_analysis(self, result: EvaluationResult) -> None:
        """Display the LLM reasoning for the evaluation"""
        panel = Panel(
            Text(result.reasoning, style="white"),
            title="[bold yellow]LLM Reasoning[/bold yellow]",
            border_style="yellow",
            padding=(0, 1),
        )
        self.console.print(panel)

    def _display_metadata(self, result: EvaluationResult) -> None:
        """Display subtle metadata"""
        self.console.print(
            f"\n[dim]Confidence: {result.confidence:.2f} • Model: {result.model_used}[/dim]"
        )
