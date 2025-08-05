from typing import TypedDict
import time
import statistics
from datetime import datetime
from rich.table import Table
from rich.console import Console
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator
from rich.progress import Progress


class ScoreStats(TypedDict):
    mean: float
    median: float
    std: float
    min: float
    max: float
    range: float


class ExecutionTimeStats(TypedDict):
    mean: float
    std: float
    min: float
    max: float


class BenchmarkStats(TypedDict):
    what: ScoreStats
    why: ScoreStats
    overall: ScoreStats
    execution_time: ExecutionTimeStats


class RunResult(TypedDict):
    run: int
    what_score: float
    why_score: float
    overall_score: float
    confidence: float
    execution_time: float


class StabilityTestResult(TypedDict):
    message: str
    runs: int
    results: list[RunResult]
    statistics: BenchmarkStats
    is_stable: bool
    max_variance: float
    variance_threshold: float
    timestamp: str


class EvaluationBenchmarks:
    """
    Benchmarking and validation tools for LLM based commit message evaluation.
    """

    def __init__(self, evaluator: CommitMessageEvaluator):
        self.console = Console()
        self.evaluator = evaluator

    def stability_test(
        self, message: str, diff: str, runs: int = 3, variance_threshold: float = 0.2
    ) -> StabilityTestResult:
        """
        Run a stability test on the evaluator.
        """
        if not message or not diff:
            raise ValueError("Message and diff are required for stability test")

        results: list[RunResult] = []
        execution_times: list[float] = []
        with Progress(console=self.console) as progress:
            task = progress.add_task("Evaluating...", total=runs)
            for run in range(runs):
                start_time = time.time()
                result = self.evaluator.evaluate_commit_message(message, diff)

                execution_time = time.time() - start_time
                execution_times.append(execution_time)

                run_data: RunResult = {
                    "run": run + 1,
                    "what_score": result.what_score,
                    "why_score": result.why_score,
                    "overall_score": result.overall_score,
                    "confidence": result.confidence,
                    "execution_time": execution_time,
                }
                results.append(run_data)

                progress.update(task, advance=1)
                self.console.print(
                    f"   Run {run + 1}: WHAT={result.what_score:.1f}, WHY={result.why_score:.1f}, OVERALL={result.overall_score:.1f} completed in {execution_time}s"
                )

        stats = self._calculate_statistics(results, execution_times)
        max_variance = self._determine_stability(stats)
        is_stable = max_variance <= variance_threshold

        self._display_stability_results(stats, is_stable, variance_threshold)

        return {
            "message": message,
            "runs": runs,
            "results": results,
            "statistics": stats,
            "is_stable": is_stable,
            "max_variance": max_variance,
            "variance_threshold": variance_threshold,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_statistics(
        self, results: list[RunResult], execution_times: list[float]
    ) -> BenchmarkStats:
        """
        Calculate statistics for the results and execution times.
        """
        what_scores = [r["what_score"] for r in results]
        why_scores = [r["why_score"] for r in results]
        overall_scores = [r["overall_score"] for r in results]

        return {
            "what": self._calculate_score_variance(what_scores),
            "why": self._calculate_score_variance(why_scores),
            "overall": self._calculate_score_variance(overall_scores),
            "execution_time": {
                "mean": statistics.mean(execution_times),
                "std": statistics.stdev(execution_times)
                if len(execution_times) > 1
                else 0,
                "min": min(execution_times),
                "max": max(execution_times),
            },
        }

    def _determine_stability(self, stats: BenchmarkStats) -> float:
        """
        Determine stability based on the statistics.
        """
        return max(
            stats["what"]["range"], stats["why"]["range"], stats["overall"]["range"]
        )

    def _calculate_score_variance(self, scores: list[float]) -> ScoreStats:
        """
        Calculate variance and other statistics for a list of scores.
        """
        if not scores:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "range": 0.0,
            }

        return {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "std": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
            "range": max(scores) - min(scores),
        }

    def _display_stability_results(
        self, stats: BenchmarkStats, is_stable: bool, threshold: float
    ) -> None:
        """
        Display the stability test results.
        """

        table = Table(title="Stability Test Results", show_header=True)
        table.add_column("Dimension", style="cyan")
        table.add_column("Mean", justify="center")
        table.add_column("Std Dev", justify="center")
        table.add_column("Range", justify="center")
        table.add_column("Status", justify="center")

        dimensions_data = [
            ("WHAT", stats["what"]),
            ("WHY", stats["why"]),
            ("OVERALL", stats["overall"]),
        ]

        for dimension_name, stat in dimensions_data:
            range_val = stat["range"]
            status = "✅ Stable" if range_val <= threshold else "⚠️ Unstable"
            status_color = "green" if range_val <= threshold else "red"

            table.add_row(
                dimension_name,
                f"{stat['mean']:.2f}",
                f"{stat['std']:.2f}",
                f"{range_val:.2f}",
                f"[{status_color}]{status}[/{status_color}]",
            )

        self.console.print(table)

        # Overall assessment
        overall_color = "green" if is_stable else "red"
        overall_status = "STABLE" if is_stable else "UNSTABLE"

        self.console.print(
            f"\n[{overall_color}]Overall Assessment: {overall_status} (threshold: ±{threshold})[/{overall_color}]"
        )

        # Performance info
        exec_stats = stats["execution_time"]
        self.console.print(
            f"\n[dim]Average execution time: {exec_stats['mean']:.2f}s (±{exec_stats['std']:.2f}s)[/dim]"
        )
