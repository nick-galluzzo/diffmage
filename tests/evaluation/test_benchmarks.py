import pytest
from rich.progress import Progress
from diffmage.evaluation.benchmarks import EvaluationBenchmarks
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator
from rich.console import Console
from unittest.mock import Mock, patch


@pytest.fixture
def evaluator():
    """Fixture providing CommitMessageEvaluator instance"""
    return CommitMessageEvaluator()


@pytest.fixture
def benchmarks(evaluator):
    """Fixture providing EvaluationBenchmarks instance"""
    return EvaluationBenchmarks(evaluator)


class TestEvaluationBenchmarks:
    """Test cases for EvaluationBenchmarks model."""

    def test_evaluation_benchmarks_initialization(self, benchmarks):
        """Test successful creation of EvaluationBenchmarks."""

        assert benchmarks is not None
        assert benchmarks.evaluator is not None
        assert isinstance(benchmarks.evaluator, CommitMessageEvaluator)
        assert isinstance(benchmarks.console, Console)

    def test_stability_test_with_empty_message_raises_error(self, benchmarks):
        """Test stability test with empty message raises error"""
        with pytest.raises(
            ValueError, match="Message and diff are required for stability test"
        ):
            benchmarks.stability_test(message="", diff="some diff")

    def test_stability_test_with_none_raises_error(self, benchmarks):
        """Test stability test with none raises error"""
        with pytest.raises(
            ValueError, match="Message and diff are required for stability test"
        ):
            benchmarks.stability_test(message=None, diff=None)

    def test_stability_test_with_empty_diff_raises_error(self, benchmarks):
        """Test stability test with empty diff raises error"""
        with pytest.raises(
            ValueError, match="Message and diff are required for stability test"
        ):
            benchmarks.stability_test(message="some message", diff="")

    def test_stability_test_calls_evaluator_correct_number_of_times(self, benchmarks):
        """Test stability test calls evaluator correct number of times"""
        message = "some message"
        diff = "some diff"
        runs = 3

        mock_result = Mock()
        mock_result.what_score = 4.0
        mock_result.why_score = 3.5
        mock_result.overall_score = 3.8
        mock_result.confidence = 0.8

        with patch.object(
            benchmarks.evaluator, "evaluate_commit_message", return_value=mock_result
        ) as mock_evaluate:
            result = benchmarks.stability_test(message=message, diff=diff, runs=runs)

            assert mock_evaluate.call_count == runs
            assert result["runs"] == runs
            assert len(result["results"]) == runs

    def test_stability_test_calculates_statistics_correctly(self, benchmarks):
        """Test stability test calculates statistics correctly"""
        message = "some message"
        diff = "some diff"

        mock_result = Mock()
        mock_result.what_score = 4.0
        mock_result.why_score = 3.5
        mock_result.overall_score = 3.8
        mock_result.confidence = 0.8

        with patch.object(
            benchmarks.evaluator, "evaluate_commit_message", return_value=mock_result
        ):
            result = benchmarks.stability_test(message=message, diff=diff, runs=2)

            stats = result["statistics"]

            assert "what" in stats
            assert "why" in stats
            assert "overall" in stats
            assert "execution_time" in stats

    @patch("time.time")
    @patch.object(Progress, "__enter__")
    @patch.object(Progress, "__exit__")
    def test_stability_test_calculates_execution_time_correctly(
        self, mock_exit, mock_enter, mock_time, benchmarks
    ):
        """Test stability test calculates execution time correctly"""

        mock_time.side_effect = [1000.0, 1000.5, 1001.0, 1001.3]

        mock_progress = Mock()
        mock_task = Mock()
        mock_progress.add_task.return_value = mock_task
        mock_enter.return_value = mock_progress

        mock_result1 = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )
        mock_result2 = Mock(
            what_score=4.5, why_score=3.5, overall_score=4.0, confidence=0.9
        )

        with patch.object(
            benchmarks.evaluator,
            "evaluate_commit_message",
            side_effect=[mock_result1, mock_result2],
        ):
            result = benchmarks.stability_test("test message", "test diff", runs=2)

            assert len(result["results"]) == 2
            assert result["results"][0]["execution_time"] == pytest.approx(0.5)
            assert result["results"][1]["execution_time"] == pytest.approx(0.3)

            assert "execution_time" in result["statistics"]
            assert result["statistics"]["execution_time"]["mean"] == pytest.approx(0.4)

    def test_stability_test_is_stable_returns_true_if_variance_is_less_than_threshold(
        self, benchmarks
    ):
        """Test stability test is stable if variance is less than threshold"""

        mock_result1 = Mock(
            what_score=4.1, why_score=3.0, overall_score=3.5, confidence=0.8
        )
        mock_result2 = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )

        with patch.object(
            benchmarks.evaluator,
            "evaluate_commit_message",
            side_effect=[mock_result1, mock_result2],
        ):
            result = benchmarks.stability_test(
                "test message", "test diff", runs=2, variance_threshold=0.2
            )
            assert result["is_stable"] is True
            assert result["max_variance"] == pytest.approx(0.1)
            assert result["variance_threshold"] == 0.2

    def test_stability_test_is_stable_returns_false_if_variance_is_greater_than_threshold(
        self, benchmarks
    ):
        """Test stability test is stable if variance is less than threshold"""

        mock_result1 = Mock(
            what_score=2.5, why_score=2.0, overall_score=2.5, confidence=0.8
        )
        mock_result2 = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )

        with patch.object(
            benchmarks.evaluator,
            "evaluate_commit_message",
            side_effect=[mock_result1, mock_result2],
        ):
            result = benchmarks.stability_test(
                "test message", "test diff", runs=2, variance_threshold=0.2
            )
            assert result["is_stable"] is False
            assert result["max_variance"] == pytest.approx(1.5)
            assert result["variance_threshold"] == 0.2

    def test_stability_test_returns_variance_threshold_as_is(self, benchmarks):
        """Test stability test returns variance threshold as is"""
        with patch.object(
            benchmarks.evaluator,
            "evaluate_commit_message",
            side_effect=[
                Mock(what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8),
                Mock(what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8),
            ],
        ):
            result = benchmarks.stability_test(
                "test message", "test diff", runs=2, variance_threshold=0.2
            )
            assert result["variance_threshold"] == 0.2

    def test_stability_test_returns_expected_structure_and_values(self, benchmarks):
        """Test stability test returns expected structure with correct values."""
        mock_result = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )

        with (
            patch.object(
                benchmarks.evaluator,
                "evaluate_commit_message",
                return_value=mock_result,
            ),
            patch("diffmage.evaluation.benchmarks.Progress"),
        ):
            result = benchmarks.stability_test("test message", "test diff", runs=3)

            # Test structure exists
            assert result is not None
            assert "message" in result
            assert "runs" in result
            assert "results" in result
            assert "statistics" in result
            assert "is_stable" in result
            assert "max_variance" in result
            assert "variance_threshold" in result
            assert "timestamp" in result

            # Test basic values are correct
            assert result["message"] == "test message"
            assert result["runs"] == 3
            assert len(result["results"]) == 3
            assert isinstance(result["is_stable"], bool)
            assert result["variance_threshold"] == 0.2  # default value
            assert isinstance(result["timestamp"], str)

    def test_stability_test_processes_results_correctly(self, benchmarks):
        """Test that individual run results are processed correctly."""
        mock_result = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )

        with (
            patch.object(
                benchmarks.evaluator,
                "evaluate_commit_message",
                return_value=mock_result,
            ),
            patch("diffmage.evaluation.benchmarks.Progress"),
        ):
            result = benchmarks.stability_test("test", "diff", runs=2)

            assert len(result["results"]) == 2

            first_run = result["results"][0]
            assert first_run["run"] == 1
            assert first_run["what_score"] == 4.0
            assert first_run["why_score"] == 3.0
            assert first_run["overall_score"] == 3.5
            assert first_run["confidence"] == 0.8
            assert "execution_time" in first_run

    def test_stability_test_statistics_structure(self, benchmarks):
        """Test that statistics are calculated and structured correctly."""
        mock_result = Mock(
            what_score=4.0, why_score=3.0, overall_score=3.5, confidence=0.8
        )

        with (
            patch.object(
                benchmarks.evaluator,
                "evaluate_commit_message",
                return_value=mock_result,
            ),
            patch("diffmage.evaluation.benchmarks.Progress"),
        ):
            result = benchmarks.stability_test("test", "diff", runs=2)

            stats = result["statistics"]

            assert "what" in stats
            assert "why" in stats
            assert "overall" in stats
            assert "execution_time" in stats

            for score_type in ["what", "why", "overall"]:
                assert "mean" in stats[score_type]
                assert "std" in stats[score_type]
                assert "min" in stats[score_type]
                assert "max" in stats[score_type]

    ### Calculate Statistics ####

    def test_calculate_statistics_returns_expected_structure(self, benchmarks):
        """Test that _calculate_statistics returns expected structure."""
        results = [
            {"what_score": 4.0, "why_score": 3.0, "overall_score": 3.5},
            {"what_score": 4.0, "why_score": 3.0, "overall_score": 3.5},
        ]
        execution_times = [0.5, 0.3]

        with patch.object(benchmarks, "_calculate_score_variance", return_value={}):
            result = benchmarks._calculate_statistics(results, execution_times)

            assert result is not None
            assert "what" in result
            assert "why" in result
            assert "overall" in result
            assert "execution_time" in result

            assert "mean" in result["execution_time"]
            assert "std" in result["execution_time"]
            assert "min" in result["execution_time"]
            assert "max" in result["execution_time"]

    def test_calculate_statistics_calls_score_variance_for_each_score_type(
        self, benchmarks
    ):
        """Test that _calculate_score_variance is called for each score type."""
        results = [
            {"what_score": 4.0, "why_score": 3.0, "overall_score": 3.5},
            {"what_score": 5.0, "why_score": 4.0, "overall_score": 4.5},
        ]
        execution_times = [0.5, 0.3]

        with patch.object(
            benchmarks, "_calculate_score_variance", return_value={}
        ) as mock_calc:
            benchmarks._calculate_statistics(results, execution_times)

            assert mock_calc.call_count == 3

            calls = mock_calc.call_args_list
            assert calls[0][0][0] == [4.0, 5.0]
            assert calls[1][0][0] == [3.0, 4.0]
            assert calls[2][0][0] == [3.5, 4.5]

    def test_calculate_statistics_calculates_execution_time_stats_correctly(
        self, benchmarks
    ):
        """Test execution time statistics are calculated correctly."""
        results = [{"what_score": 4.0, "why_score": 3.0, "overall_score": 3.5}]
        execution_times = [0.5, 0.3]

        with patch.object(benchmarks, "_calculate_score_variance", return_value={}):
            result = benchmarks._calculate_statistics(results, execution_times)

            assert result["execution_time"]["mean"] == pytest.approx(0.4)
            assert result["execution_time"]["std"] == pytest.approx(0.14142135623)
            assert result["execution_time"]["min"] == 0.3
            assert result["execution_time"]["max"] == 0.5

    def test_calculate_statistics_uses_score_variance_results(self, benchmarks):
        """Test that score variance results are properly integrated."""
        results = [{"what_score": 4.0, "why_score": 3.0, "overall_score": 3.5}]
        execution_times = [0.5]

        mock_variance = {
            "mean": 4.2,
            "median": 4.0,
            "std": 0.1,
            "min": 4.0,
            "max": 4.4,
            "range": 0.4,
        }

        with patch.object(
            benchmarks, "_calculate_score_variance", return_value=mock_variance
        ):
            result = benchmarks._calculate_statistics(results, execution_times)

            assert result["what"] == mock_variance
            assert result["why"] == mock_variance
            assert result["overall"] == mock_variance

    #### Score Variance #####

    def test_calculate_score_if_no_scores_returns_empty_dict(self, benchmarks):
        """Test calculate_score_variance returns empty dict if no scores"""
        scores = []
        result = benchmarks._calculate_score_variance(scores)
        assert result == {}

    def test_calculate_score_variance_returns_expected_structure(self, benchmarks):
        """Test calculate_score_variance returns expected structure"""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = benchmarks._calculate_score_variance(scores)
        assert result is not None
        assert "mean" in result
        assert "median" in result
        assert "std" in result
        assert "min" in result
        assert "max" in result
        assert "range" in result

    def test_calculate_score_variance_returns_correct_values(self, benchmarks):
        """Test calculate_score_variance returns correct values"""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = benchmarks._calculate_score_variance(scores)
        assert result["mean"] == pytest.approx(3.0)
        assert result["median"] == pytest.approx(3.0)
        assert result["std"] == pytest.approx(1.58113883008)
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        assert result["range"] == 4.0
