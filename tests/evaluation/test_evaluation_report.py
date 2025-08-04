import pytest
from rich.console import Console
from diffmage.evaluation.service import EvaluationService
from diffmage.evaluation.evaluation_report import EvaluationReport
from diffmage.evaluation.models import EvaluationResult
from unittest.mock import patch


@pytest.fixture
def service():
    """Fixture providing EvaluationService instance"""
    return EvaluationService()


@pytest.fixture
def report(service):
    """Fixture providing EvaluationReport instance"""
    return EvaluationReport(service)


@pytest.fixture
def sample_results():
    """Fixture providing sample evaluation results for testing"""
    return [
        (
            EvaluationResult(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            "feat: add user authentication",
        ),
        (
            EvaluationResult(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            "fix bug",
        ),
        (
            EvaluationResult(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1.0,
                model_used="gpt-4o-mini",
            ),
            "docs: update README with installation instructions",
        ),
    ]


class TestEvaluationReport:
    """Test cases for EvaluationReport model."""

    def test_evaluation_report_initialization(self, service, report):
        """Test successful creation of EvaluationReport."""
        assert report.service == service
        assert isinstance(report.console, Console)

    def test_generate_report_empty_results_raises_error(self, report):
        """Test that empty results raise ValueError"""
        with pytest.raises(ValueError, match="No evaluation results to report"):
            report.generate_quality_report([])

    def test_generate_report_with_unicode_messages(self, report):
        """Test handling of Unicode characters in commit messages"""
        unicode_results = [
            (
                EvaluationResult(
                    what_score=4,
                    why_score=4,
                    reasoning="Good commit with unicode",
                    confidence=0.9,
                    model_used="gpt-4o",
                ),
                "feat: 添加用户认证功能 🔒",
            ),
            (
                EvaluationResult(
                    what_score=3,
                    why_score=3,
                    reasoning="Emoji handling",
                    confidence=0.8,
                    model_used="gpt-4o",
                ),
                "fix: 🐛 修复登录bug with ñoño café",
            ),
        ]

        result = report.generate_quality_report(unicode_results)
        assert "Report generated successfully for 2 evaluations" in result

    @pytest.mark.parametrize(
        "what_score,why_score,expected_overall",
        [
            (1, 1, 1.0),
            (3, 4, 3.5),
            (5, 5, 5.0),
            (2, 4, 3.0),
            (4.5, 3.5, 4.0),
        ],
    )
    def test_overall_score_calculation(
        self, report, what_score, why_score, expected_overall
    ):
        """Test overall score calculation with various inputs"""
        result_data = [
            (
                EvaluationResult(
                    what_score=what_score,
                    why_score=why_score,
                    reasoning="Test calculation",
                    confidence=0.9,
                    model_used="gpt-4o",
                ),
                "test commit",
            )
        ]

        stats = report._calculate_report_statistics(result_data)
        assert stats["overall_scores"]["mean"] == expected_overall

    @pytest.mark.parametrize(
        "model_name,expected_count",
        [
            ("gpt-4o", 1),
            ("gpt-4o-mini", 1),
            ("openrouter/qwen/qwen3-coder:free", 1),
            ("", 1),
            ("claude-3-sonnet", 1),
        ],
    )
    def test_model_usage_counting(self, report, model_name, expected_count):
        """Test model usage counting for different model names"""
        result_data = [
            (
                EvaluationResult(
                    what_score=4,
                    why_score=4,
                    reasoning="Test model counting",
                    confidence=0.9,
                    model_used=model_name,
                ),
                "test commit",
            )
        ]

        stats = report._calculate_report_statistics(result_data)
        assert stats["model_usage"][model_name] == expected_count

    def test_calculate_report_statistics_with_results(self, report):
        """Test that statistics are calculated correctly"""
        mock_results = [self._create_mock_result()]

        with patch.object(report, "_calculate_report_statistics") as mock_calc:
            mock_calc.return_value = {
                "total_evaluations": 1,
                "what_scores": {
                    "mean": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0,
                },
                "why_scores": {
                    "mean": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0,
                },
                "overall_scores": {
                    "mean": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0,
                },
                "quality_distribution": {
                    "Excellent": 0,
                    "Good": 0,
                    "Average": 0,
                    "Poor": 0,
                    "Very Poor": 0,
                },
                "model_usage": {
                    "gpt-4o": 1,
                },
                "high_quality_count": 0,
                "low_quality_count": 0,
            }
            report.generate_quality_report(mock_results)

            mock_calc.assert_called_once_with(mock_results)

    #### Calculate Report Statistics ####

    def test_calculate_report_statistics_basic_counts(self, report):
        """Test basic counting and structure"""
        mock_results = [
            self._create_mock_result(),
            self._create_mock_result(
                what_score=3,
                why_score=3,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["total_evaluations"] == 3
        assert "what_scores" in stats
        assert "why_scores" in stats
        assert "overall_scores" in stats
        assert "confidence" in stats
        assert "quality_distribution" in stats
        assert "model_usage" in stats
        assert "high_quality_count" in stats
        assert "low_quality_count" in stats

    def test_calculate_statistics_mean_calculations(self, report):
        """Test score calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["mean"] == pytest.approx(4)
        assert stats["why_scores"]["mean"] == pytest.approx(3.67)
        assert stats["overall_scores"]["mean"] == pytest.approx(3.83)

    def test_calculate_statistics_median_calculations(self, report):
        """Test median score calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["median"] == 4
        assert stats["why_scores"]["median"] == 4
        assert stats["overall_scores"]["median"] == 4

    def test_calculate_statistics_min_calculations(self, report):
        """Test minimum score calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["min"] == 3
        assert stats["why_scores"]["min"] == 2
        assert stats["overall_scores"]["min"] == 2.5

    def test_calculate_statistics_max_calculations(self, report):
        """Test maximum score calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["max"] == 5
        assert stats["why_scores"]["max"] == 5
        assert stats["overall_scores"]["max"] == 5

    def test_quality_distribution_calculations(self, report):
        """Test quality distribution calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["quality_distribution"]["Excellent"] == 0
        assert stats["quality_distribution"]["Good"] == 1
        assert stats["quality_distribution"]["Average"] == 1
        assert stats["quality_distribution"]["Poor"] == 0

    def test_model_usage_calculations(self, report):
        """Test model usage calculations"""
        mock_results = [
            self._create_mock_result(model_used="gpt-4o"),
            self._create_mock_result(model_used="gpt-4o-mini"),
            self._create_mock_result(model_used="openrouter/qwen/qwen3-coder:free"),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["model_usage"]["gpt-4o"] == 1
        assert stats["model_usage"]["gpt-4o-mini"] == 1
        assert stats["model_usage"]["openrouter/qwen/qwen3-coder:free"] == 1
        assert stats["model_usage"]["openrouter/deepseek/deepseek-r1-0528:free"] == 0

    def test_high_quality_count_calculations(self, report):
        """Test high quality count calculations"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Good commit message",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Bad commit message",
                confidence=0.8,
                model_used="gpt-4o-mini",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Perfect commit message",
                confidence=1,
                model_used="openrouter/qwen/qwen3-coder:free",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["high_quality_count"] == 1
        assert stats["low_quality_count"] == 2

    def test_single_result_statistics(self, report):
        """Test statistics calculation with only one result"""
        mock_results = [
            self._create_mock_result(
                what_score=3,
                why_score=4,
                reasoning="Single result",
                confidence=0.85,
                model_used="gpt-4o",
            )
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["total_evaluations"] == 1
        assert stats["what_scores"]["mean"] == 3
        assert stats["what_scores"]["median"] == 3
        assert stats["what_scores"]["min"] == 3
        assert stats["what_scores"]["max"] == 3
        assert stats["why_scores"]["mean"] == 4
        assert stats["overall_scores"]["mean"] == 3.5
        assert stats["confidence"]["mean"] == 0.85
        assert stats["model_usage"]["gpt-4o"] == 1

    def test_identical_scores_statistics(self, report):
        """Test when all scores are identical"""
        mock_results = [
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Same score 1",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Same score 2",
                confidence=0.9,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Same score 3",
                confidence=0.9,
                model_used="gpt-4o",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["mean"] == 4
        assert stats["what_scores"]["median"] == 4
        assert stats["what_scores"]["min"] == 4
        assert stats["what_scores"]["max"] == 4
        assert stats["why_scores"]["mean"] == 4
        assert stats["overall_scores"]["mean"] == 4
        assert stats["confidence"]["mean"] == 0.9

    def test_boundary_score_values(self, report):
        """Test with minimum and maximum possible scores"""
        mock_results = [
            self._create_mock_result(
                what_score=1,
                why_score=1,
                reasoning="Minimum scores",
                confidence=0.5,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=5,
                why_score=5,
                reasoning="Maximum scores",
                confidence=1.0,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["min"] == 1
        assert stats["what_scores"]["max"] == 5
        assert stats["why_scores"]["min"] == 1
        assert stats["why_scores"]["max"] == 5
        assert stats["overall_scores"]["min"] == 1
        assert stats["overall_scores"]["max"] == 5
        assert stats["confidence"]["min"] == 0.5
        assert stats["confidence"]["max"] == 1.0

    def test_confidence_boundary_values(self, report):
        """Test with 0.0 and 1.0 confidence values"""
        mock_results = [
            self._create_mock_result(
                what_score=3,
                why_score=3,
                reasoning="Zero confidence",
                confidence=0.0,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Perfect confidence",
                confidence=1.0,
                model_used="gpt-4o-mini",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["confidence"]["min"] == 0.0
        assert stats["confidence"]["max"] == 1.0
        assert stats["confidence"]["mean"] == 0.5

    def test_rounding_precision(self, report):
        """Test decimal rounding behavior"""
        mock_results = [
            self._create_mock_result(
                what_score=3,
                why_score=2,
                reasoning="Test rounding",
                confidence=0.333,
                model_used="gpt-4o",
            ),
            self._create_mock_result(
                what_score=2,
                why_score=3,
                reasoning="Test rounding",
                confidence=0.666,
                model_used="gpt-4o",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["what_scores"]["mean"] == 2.5
        assert stats["why_scores"]["mean"] == 2.5
        assert stats["overall_scores"]["mean"] == 2.5
        assert isinstance(stats["what_scores"]["mean"], float)
        assert isinstance(stats["confidence"]["mean"], float)

    def test_empty_model_names(self, report):
        """Test handling of empty or None model names"""
        mock_results = [
            self._create_mock_result(
                what_score=3,
                why_score=3,
                reasoning="Empty model",
                confidence=0.8,
                model_used="",
            ),
            self._create_mock_result(
                what_score=4,
                why_score=4,
                reasoning="Valid model",
                confidence=0.9,
                model_used="gpt-4o",
            ),
        ]

        stats = report._calculate_report_statistics(mock_results)

        assert stats["model_usage"][""] == 1
        assert stats["model_usage"]["gpt-4o"] == 1
        assert stats["total_evaluations"] == 2

    #### Private methods ####

    def _create_mock_result(
        self,
        what_score=4,
        why_score=4,
        reasoning="Good commit message",
        confidence=0.9,
        model_used="gpt-4o",
    ):
        return (
            EvaluationResult(
                what_score=what_score,
                why_score=why_score,
                reasoning=reasoning,
                confidence=confidence,
                model_used=model_used,
            ),
            str("commit message"),
        )
