from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from diffmage.evaluation.service import EvaluationService
from diffmage.evaluation.models import EvaluationResult, QualityRater
from collections import Counter
from statistics import mean, median
from rich.table import Table
from rich import box


class EvaluationReport:
    """
    Report for evaluation results
    """

    def __init__(self, service: EvaluationService):
        self.service = service
        self.console = Console()

    def generate_report(
        self,
        results: list[tuple[EvaluationResult, str]],
        title: str = "Commit Message Quality Report",
    ) -> str:
        """
        Generate rich formatted quality report for console display

        Args:
          results: List of (EvaluationResult, commit message) tuples
          title: Optional title for the report

          Returns:
            Formatted report string
        """
        if not results:
            raise ValueError("No evaluation results to report")

        statistics = self._calculate_report_statistics(results)

        #### --Displays-- ####

        # Header
        self.console.print(
            Panel(
                Text(title, justify="center", style="bold white"),
                style="blue",
                padding=(1, 2),
            )
        )

        # Summary
        self._display_summary_table(statistics)

        # Quality Distribution
        self._display_quality_distribution_table(statistics)

        # Top and Bottom Performers
        self._display_top_and_bottom_performers(results)

        # Detailed Results
        self._display_detailed_results(results)

        return f"Report generated successfully for {len(results)} evaluation{'' if len(results) == 1 else 's'}"

    def _calculate_report_statistics(
        self, results: list[tuple[EvaluationResult, str]]
    ) -> dict[str, Any]:
        """Calculate statistics for the report"""
        what_scores = [r[0].what_score for r in results]
        why_scores = [r[0].why_score for r in results]
        overall_scores = [r[0].overall_score for r in results]
        confidence = [r[0].confidence for r in results]

        quality_counts = Counter(result[0].quality_level for result in results)
        model_usage = Counter(result[0].model_used for result in results)

        return {
            "total_evaluations": len(results),
            "what_scores": {
                "mean": round(mean(what_scores), 2),
                "median": round(median(what_scores), 2),
                "min": round(min(what_scores), 2),
                "max": round(max(what_scores), 2),
            },
            "why_scores": {
                "mean": round(mean(why_scores), 2),
                "median": round(median(why_scores), 2),
                "min": round(min(why_scores), 2),
                "max": round(max(why_scores), 2),
            },
            "overall_scores": {
                "mean": round(mean(overall_scores), 2),
                "median": round(median(overall_scores), 2),
                "min": round(min(overall_scores), 2),
                "max": round(max(overall_scores), 2),
            },
            "confidence": {
                "mean": mean(confidence),
                "median": median(confidence),
                "min": min(confidence),
                "max": max(confidence),
            },
            "quality_distribution": quality_counts,
            "model_usage": model_usage,
            "high_quality_count": sum(
                1 for result in results if result[0].is_high_quality
            ),
            "low_quality_count": sum(
                1 for result in results if not result[0].is_high_quality
            ),
        }

    def _display_summary_table(self, stats: dict[str, dict[str, Any]]) -> None:
        """Display a summary table of the statistics"""

        table = Table(title="Summary Statistics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("WHAT Score", justify="center")
        table.add_column("WHY Score", justify="center")
        table.add_column("Overall Score", justify="center")

        table.add_row(
            "Mean",
            f"{stats['what_scores']['mean']:.2f}",
            f"{stats['why_scores']['mean']:.2f}",
            f"{stats['overall_scores']['mean']:.2f}",
        )

        table.add_row(
            "Median",
            f"{stats['what_scores']['median']:.2f}",
            f"{stats['why_scores']['median']:.2f}",
            f"{stats['overall_scores']['median']:.2f}",
        )

        table.add_row(
            "Range",
            f"{stats['what_scores']['min']:.1f} - {stats['what_scores']['max']:.1f}",
            f"{stats['why_scores']['min']:.1f} - {stats['why_scores']['max']:.1f}",
            f"{stats['overall_scores']['min']:.1f} - {stats['overall_scores']['max']:.1f}",
        )

        self.console.print(table)
        self.console.print()

    def _display_quality_distribution_table(
        self, stats: dict[str, dict[str, Any]]
    ) -> None:
        """Display a table of the quality distribution"""

        table = Table(title="Quality Distribution", box=box.SIMPLE)
        table.add_column("Quality", style="cyan")
        table.add_column("Count", justify="center")
        table.add_column("Percentage", justify="center")

        total = stats["total_evaluations"]

        quality_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]

        for quality in quality_order:
            count = stats["quality_distribution"].get(quality, 0)
            percentage = round((count / total) * 100, 1)
            table.add_row(quality, str(count), f"{percentage}%")

        self.console.print(table)

    def _display_top_and_bottom_performers(
        self, results: list[tuple[EvaluationResult, str]]
    ) -> None:
        """Display the top and bottom performers"""

        sorted_results = sorted(results, key=lambda x: x[0].overall_score, reverse=True)

        self.console.print("[bold green]🏆 Top Performing Messages:[/bold green]")
        for i, (result, message) in enumerate(sorted_results[:3], 1):
            truncated_msg = message[:60] + "..." if len(message) > 60 else message
            self.console.print(f"  {i}. [{result.overall_score:.1f}/5] {truncated_msg}")

        self.console.print()

        if len(sorted_results) > 3:
            self.console.print("[bold red]⚠️  Lowest Performing Messages:[/bold red]")
            for i, (result, message) in enumerate(sorted_results[-3:], 1):
                truncated_msg = message[:60] + "..." if len(message) > 60 else message
                self.console.print(
                    f"  {i}. [{result.overall_score:.1f}/5] {truncated_msg}"
                )

        self.console.print()

    def _display_detailed_results(
        self, results: list[tuple[EvaluationResult, str]]
    ) -> None:
        """Display detailed results"""

        table = Table(title="Detailed Results", box=box.SIMPLE, show_lines=True)
        table.add_column("Message", style="white", width=40)
        table.add_column("WHAT", justify="center", width=6)
        table.add_column("WHY", justify="center", width=6)
        table.add_column("Overall", justify="center", width=8)
        table.add_column("Quality", width=10)
        table.add_column("Confidence", justify="center", width=10)

        sorted_results = sorted(results, key=lambda x: x[0].overall_score, reverse=True)

        for result, message in sorted_results:
            display_message = message[:37] + "..." if len(message) > 37 else message

            overall_color = QualityRater.get_rating_color(result.overall_score)

            table.add_row(
                display_message,
                f"{result.what_score:.1f}",
                f"{result.why_score:.1f}",
                f"[{overall_color}]{result.overall_score:.1f}[/{overall_color}]",
                f"[{overall_color}]{result.quality_level}[/{overall_color}]",
                f"{result.confidence:.2f}",
            )

        self.console.print(table)
