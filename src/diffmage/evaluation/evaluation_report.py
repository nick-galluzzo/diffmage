from rich.console import Console
from diffmage.evaluation.service import EvaluationService
from diffmage.evaluation.models import EvaluationResult
from collections import Counter
from statistics import mean, median


class EvaluationReport:
    """
    Report for evaluation results
    """

    def __init__(self, service: EvaluationService):
        self.service = service
        self.console = Console()

    def generate_report(self, results: list[tuple[EvaluationResult, str]]) -> str:
        """Generate a report for the evaluation results"""
        if not results:
            raise ValueError("No evaluation results to report")

        statistics = self._calculate_report_statistics(results)
        self.console.print(statistics)

        return "Report generated successfully"

    def _calculate_report_statistics(
        self, results: list[tuple[EvaluationResult, str]]
    ) -> dict:
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
