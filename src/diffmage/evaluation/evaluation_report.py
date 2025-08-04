from typing import Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from diffmage.evaluation.service import EvaluationService
from diffmage.evaluation.models import EvaluationResult, QualityRater
from collections import Counter
from statistics import mean, median
from rich.table import Table
from rich import box
from pathlib import Path
import csv
import json
from datetime import datetime
import git
from diffmage.evaluation.service import get_default_model


class EvaluationReport:
    """
    Report for evaluation results
    """

    def __init__(self, service: EvaluationService):
        self.service = service
        self.console = Console()

    def generate_quality_report(
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

    def get_top_performers(
        self, results: list[tuple[EvaluationResult, str]], count: int = 3
    ) -> list[tuple[EvaluationResult, str]]:
        """Get top performing results by overall score"""
        if not results:
            return []

        sorted_results = sorted(results, key=lambda x: x[0].overall_score, reverse=True)
        return sorted_results[: min(count, len(sorted_results))]

    def get_bottom_performers(
        self, results: list[tuple[EvaluationResult, str]], count: int = 3
    ) -> list[tuple[EvaluationResult, str]]:
        """Get bottom performing results by overall score, excluding overlap with top performers"""
        if len(results) <= 1:
            return []

        sorted_results = sorted(results, key=lambda x: x[0].overall_score, reverse=True)

        # Get top performer indices to avoid overlap
        num_top = min(count, len(sorted_results))
        top_indices = set(range(num_top))

        # Get bottom performers, excluding those already in top
        num_bottom = min(count, len(sorted_results))
        bottom_performers = [
            sorted_results[i]
            for i in range(len(sorted_results) - num_bottom, len(sorted_results))
            if i not in top_indices
        ]

        # Sort bottom performers ascending (worst to best)
        return sorted(bottom_performers, key=lambda x: x[0].overall_score)

    def get_top_and_bottom_performers(
        self, results: list[tuple[EvaluationResult, str]], count: int = 3
    ) -> tuple[list[tuple[EvaluationResult, str]], list[tuple[EvaluationResult, str]]]:
        """Get top and bottom performers ensuring no overlap between them"""
        top_performers = self.get_top_performers(results, count)
        bottom_performers = self.get_bottom_performers(results, count)

        # Ensure no overlap by checking actual instances
        top_instances = set(id(item) for item in top_performers)
        bottom_performers = [
            item for item in bottom_performers if id(item) not in top_instances
        ]

        return top_performers, bottom_performers

    def _display_top_and_bottom_performers(
        self, results: list[tuple[EvaluationResult, str]]
    ) -> None:
        """Display the top and bottom performers"""

        top_performers, bottom_performers = self.get_top_and_bottom_performers(results)

        # Display top performers
        self.console.print("[bold green]🏆 Top Performing Messages:[/bold green]")
        self.console.print()

        for i, (result, message) in enumerate(top_performers, 1):
            self.console.print(f"  {i}. [{result.overall_score:.1f}/5] {message}")
            self.console.print()

        self.console.print()

        # Display bottom performers if we have any
        if bottom_performers:
            self.console.print("[bold red]⚠️  Lowest Performing Messages:[/bold red]")
            self.console.print()

            for i, (result, message) in enumerate(bottom_performers, 1):
                self.console.print(f"  {i}. [{result.overall_score:.1f}/5] {message}")
                self.console.print()

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

    def export_csv_report(
        self,
        results: list[tuple[EvaluationResult, str]],
        filename: str = "evaluation_report.csv",
    ) -> str:
        """
        Export evaluation data to CSV for analysis

        Args:
            results: List of (EvaluationResult, commit_message) tuples
            filename: Output CSV filename

        Returns:
            Path to created CSV file
        """

        filepath = Path(filename)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "commit_message",
                "what_score",
                "why_score",
                "overall_score",
                "quality_level",
                "reasoning",
                "confidence",
                "model_used",
                "timestamp",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result, message in results:
                writer.writerow(
                    {
                        "commit_message": message,
                        "what_score": result.what_score,
                        "why_score": result.why_score,
                        "overall_score": result.overall_score,
                        "quality_level": result.quality_level,
                        "reasoning": result.reasoning,
                        "confidence": result.confidence,
                        "model_used": result.model_used,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return str(filepath.absolute())

    def export_json_report(
        self,
        results: list[tuple[EvaluationResult, str]],
        filename: str = "evaluation_report.json",
    ) -> str:
        """Export evaluation data to JSON"""

        filepath = Path(filename)
        stats = self._calculate_report_statistics(results)

        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_evaluations": len(results),
            },
            "statistics": stats,
            "evaluations": [
                {"commit_message": message, "evaluation": result.to_dict()}
                for result, message in results
            ],
        }

        with open(filepath, "w", encoding="utf-8") as jsonfile:
            json.dump(report_data, jsonfile, indent=2, ensure_ascii=False)

        return str(filepath.absolute())

    def batch_evaluate_commits(
        self,
        from_commit: str,  # Older commit (Inclusive)
        to_commit: str,  # Newer commit (Inclusive)
        repo_path: str = ".",
        model_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Evaluate multiple commits and generate comprehensive report

        Args:
            from_commit: Start of git commit range (e.g., "HEAD~10", "abc456"). Inclusive.
            to_commit: End of git commit range (e.g., "HEAD", "abc123"). Inclusive.
            repo_path: Path to git repository
            model_name: AI model to use for evaluation

        Returns:
            Dictionary with evaluation results and statistics
        """

        if not model_name:
            model_name = get_default_model().name

        commit_range = f"{from_commit}~1..{to_commit}"

        # Get commit list
        try:
            repo = git.Repo(repo_path)
            commits = list(repo.iter_commits(commit_range))
        except Exception as e:
            raise ValueError(f"Failed to get commits for range '{commit_range}': {e}")

        if not commits:
            raise ValueError(f"No commits found in range: {commit_range}")

        self.console.print(
            f"[blue]Evaluating {len(commits)} commits from range: {commit_range}[/blue]"
        )

        # Evaluate each commit
        service = EvaluationService(model_name=model_name)
        results = []

        with self.console.status("[bold green]Evaluating commits...") as status:
            for i, commit in enumerate(commits, 1):
                status.update(
                    f"[bold green]Evaluating commit {i}/{len(commits)}: {commit.hexsha[:8]}"
                )

                try:
                    result, message = service.evaluate_commit(commit.hexsha, repo_path)
                    results.append((result, message))
                except Exception as e:
                    self.console.print(
                        f"[red]Warning: Failed to evaluate {commit.hexsha[:8]}: {e}[/red]"
                    )
                    continue

        if not results:
            raise ValueError("No commits could be evaluated successfully")

        # Generate report
        report_title = f"Batch Evaluation Report: {commit_range}"
        self.generate_quality_report(results, report_title)

        # Calculate and return statistics
        stats = self._calculate_report_statistics(results)

        return {
            "commit_range": commit_range,
            "total_commits": len(commits),
            "successful_evaluations": len(results),
            "statistics": stats,
            "results": results,
        }
