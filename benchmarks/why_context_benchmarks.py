"""
WHY Context Enhancement Benchmarking Suite
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from enum import Enum
from diffmage.generation.commit_message_generator import CommitMessageGenerator
from diffmage.generation.models import GenerationResult
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator

console = Console()


class ContextQuality(str, Enum):
    GOOD = "good"
    BAD = "bad"
    TECHNICAL = "technical"
    REDUNDANT = "redundant"


@dataclass
class WhyContextTestCase:
    """Test case for WHY context enhancement"""

    name: str
    commit_message: str
    git_diff: str
    why_context: str
    should_enhance: bool  # Should this context actually improve the message?
    expected_improvement: float  # Expected WHY score improvement (0 if no enhancement)
    context_quality: ContextQuality


class WhyContextBenchmarkSuite:
    """Benchmark suite specifically for WHY context enhancement"""

    def __init__(self, model_name: Optional[str] = None):
        self.generator = CommitMessageGenerator(model_name=model_name)
        self.evaluator = CommitMessageEvaluator(model_name=model_name)

    def get_why_context_test_cases(self) -> List[WhyContextTestCase]:
        """Get comprehensive test cases for WHY context enhancement"""

        return [
            # GOOD WHY CONTEXT (should enhance)
            WhyContextTestCase(
                name="user_problem_context",
                commit_message="fix: resolve null pointer exception in user validation",
                git_diff="""--- a/src/auth/UserValidator.java
                +++ b/src/auth/UserValidator.java
                @@ -23,7 +23,7 @@ public class UserValidator {
                    public boolean isValidUser(User user) {
                -        return user.getEmail().contains("@");
                +        return user != null && user.getEmail() != null && user.getEmail().contains("@");
                    }
                }""",
                why_context="Users were experiencing app crashes during login attempts. Support team received 47 crash reports in the last week, all traced to this validation issue. This fix prevents the crashes and improves user experience.",
                should_enhance=True,
                expected_improvement=1.5,
                context_quality=ContextQuality.GOOD,
            ),
            WhyContextTestCase(
                name="performance_impact_context",
                commit_message="perf: optimize database query for user search",
                git_diff="""--- a/src/models/User.js
                +++ b/src/models/User.js
                @@ -15,8 +15,12 @@ const userSchema = new mongoose.Schema({
                +userSchema.index({ email: 1 });
                +userSchema.index({ firstName: 1, lastName: 1 });
                userSchema.statics.searchUsers = function(searchTerm) {
                -  return this.find({
                +  return this.find({
                    $or: [
                      { email: regex },
                      { firstName: regex }
                    ]
                -  });
                +  }).limit(20).sort({ createdAt: -1 });
                };""",
                why_context="User search was taking 8-12 seconds with 100k+ users. Customer support reported users abandoning the search feature. This optimization reduces search time to under 500ms, improving user engagement.",
                should_enhance=True,
                expected_improvement=2.0,
                context_quality=ContextQuality.GOOD,
            ),
            WhyContextTestCase(
                name="compliance_requirement_context",
                commit_message="feat: add data encryption for user profiles",
                git_diff="""--- a/src/models/UserProfile.py
                +++ b/src/models/UserProfile.py
                @@ -1,4 +1,5 @@
                from django.db import models
                +from cryptography.fernet import Fernet

                class UserProfile(models.Model):
                    user = models.OneToOneField(User, on_delete=models.CASCADE)
                -    ssn = models.CharField(max_length=11)
                +    ssn_encrypted = models.BinaryField()

                +    def set_ssn(self, ssn):
                +        f = Fernet(settings.ENCRYPTION_KEY)
                +        self.ssn_encrypted = f.encrypt(ssn.encode())
                +
                +    def get_ssn(self):
                +        f = Fernet(settings.ENCRYPTION_KEY)
                +        return f.decrypt(self.ssn_encrypted).decode()""",
                why_context="Legal compliance requirement for GDPR and HIPAA. Audit found unencrypted PII in database. This change is required before Q2 compliance review to avoid potential $2.7M fine.",
                should_enhance=True,
                expected_improvement=1.8,
                context_quality=ContextQuality.GOOD,
            ),
            # BAD WHY CONTEXT (should NOT enhance)
            WhyContextTestCase(
                name="technical_implementation_context",
                commit_message="refactor: extract validation logic into separate class",
                git_diff="""--- a/src/controllers/UserController.py
                +++ b/src/controllers/UserController.py
                @@ -8,6 +8,4 @@ class UserController:
                    def create_user(self, data):
                -        if not data.get('email'):
                -            raise ValueError('Email required')
                +        UserValidator.validate_email(data)
                        return User.create(data)""",
                why_context="The previous implementation had validation logic directly in the controller. This refactor moves it to a separate UserValidator class following single responsibility principle and makes the code more maintainable.",
                should_enhance=False,
                expected_improvement=0.0,
                context_quality=ContextQuality.TECHNICAL,
            ),
            WhyContextTestCase(
                name="redundant_context",
                commit_message="fix: handle null values in email validation",
                git_diff="""--- a/src/utils/validator.js
                +++ b/src/utils/validator.js
                @@ -5,7 +5,7 @@ function validateEmail(email) {
                -    return email.includes('@');
                +    return email && email.includes('@');
                }""",
                why_context="This change fixes null pointer exceptions when email is null by adding a null check before calling includes method.",
                should_enhance=False,
                expected_improvement=0.0,
                context_quality=ContextQuality.REDUNDANT,
            ),
            WhyContextTestCase(
                name="test_coverage_context",
                commit_message="test: add unit tests for authentication service",
                git_diff="""--- /dev/null
                +++ b/tests/auth.test.js
                @@ -0,0 +1,25 @@
                +describe('AuthService', () => {
                +  test('should authenticate valid user', () => {
                +    // test implementation
                +  });
                +});""",
                why_context="Added comprehensive test coverage for the authentication service to ensure code quality and catch regressions. Tests cover both success and failure scenarios.",
                should_enhance=False,
                expected_improvement=0.0,
                context_quality=ContextQuality.TECHNICAL,
            ),
            # BORDERLINE CASES
            WhyContextTestCase(
                name="mixed_context",
                commit_message="fix: update API response format for user endpoints",
                git_diff="""--- a/src/api/users.py
                +++ b/src/api/users.py
                @@ -15,7 +15,10 @@ def get_user(user_id):
                    user = User.find(user_id)
                -    return {'user': user.to_dict()}
                +    return {
                +        'user': user.to_dict(),
                +        'timestamp': datetime.now().isoformat()
                +    }""",
                why_context="The mobile app team requested timestamp information for caching purposes. This was causing cache invalidation issues. Also updated the response format to be more consistent with other endpoints.",
                should_enhance=True,
                expected_improvement=1.0,
                context_quality=ContextQuality.GOOD,  # Mixed but has user problem
            ),
        ]

    def run_enhancement_quality_test(
        self, test_cases: List[WhyContextTestCase]
    ) -> Dict[str, Any]:
        """Test quality of WHY context enhancement"""

        console.print(
            Panel(
                "[bold]Testing WHY Context Enhancement Quality[/bold]\n"
                "Comparing original vs enhanced commit messages",
                title="🔍 Enhancement Quality Test",
                border_style="blue",
            )
        )

        results = []
        correct_decisions = 0
        total_improvement = 0

        for case in test_cases:
            console.print(f"[blue]Testing: {case.name}[/blue]")

            # Generate original message evaluation
            original_eval = self.evaluator.evaluate_commit_message(
                case.commit_message, case.git_diff
            )

            # Generate enhanced message
            enhanced_result = self.generator.enhance_with_why_context(
                GenerationResult(message=case.commit_message), case.why_context
            )

            # Evaluate enhanced message
            enhanced_eval = self.evaluator.evaluate_commit_message(
                enhanced_result.message, case.git_diff
            )

            # Calculate improvement
            why_improvement = enhanced_eval.why_score - original_eval.why_score
            overall_improvement = (
                enhanced_eval.overall_score - original_eval.overall_score
            )

            # Check if enhancement decision was correct
            was_enhanced = enhanced_result.message != case.commit_message
            correct_decision = was_enhanced == case.should_enhance

            if correct_decision:
                correct_decisions += 1

            total_improvement += why_improvement

            result = {
                "case_name": case.name,
                "context_quality": case.context_quality,
                "should_enhance": case.should_enhance,
                "was_enhanced": was_enhanced,
                "correct_decision": correct_decision,
                "original_why_score": original_eval.why_score,
                "enhanced_why_score": enhanced_eval.why_score,
                "why_improvement": why_improvement,
                "overall_improvement": overall_improvement,
                "original_message": case.commit_message,
                "enhanced_message": enhanced_result.message,
                "expected_improvement": case.expected_improvement,
            }

            results.append(result)

        # Calculate summary statistics
        decision_accuracy = (correct_decisions / len(test_cases)) * 100
        avg_improvement = total_improvement / len(test_cases)
        good_context_cases = [
            r for r in results if r["context_quality"] == ContextQuality.GOOD
        ]
        bad_context_cases = [
            r
            for r in results
            if r["context_quality"]
            in [ContextQuality.TECHNICAL, ContextQuality.REDUNDANT]
        ]

        summary = {
            "decision_accuracy": decision_accuracy,
            "average_why_improvement": avg_improvement,
            "good_context_avg_improvement": sum(
                r["why_improvement"] for r in good_context_cases
            )
            / len(good_context_cases)
            if good_context_cases
            else 0,
            "bad_context_avg_improvement": sum(
                r["why_improvement"] for r in bad_context_cases
            )
            / len(bad_context_cases)
            if bad_context_cases
            else 0,
            "enhancement_rate": sum(1 for r in results if r["was_enhanced"])
            / len(results)
            * 100,
        }

        self._display_enhancement_results(results, summary)

        return {
            "summary": summary,
            "individual_results": results,
            "passed": decision_accuracy >= 70
            and summary["good_context_avg_improvement"] > 0.5,
        }

    def _display_enhancement_results(
        self, results: List[Dict], summary: Dict[str, Any]
    ):
        """Display enhancement quality results"""

        table = Table(title="WHY Context Enhancement Results", box=box.SIMPLE)
        table.add_column("Case", style="cyan")
        table.add_column("Quality", justify="center")
        table.add_column("Should Enhance", justify="center")
        table.add_column("Was Enhanced", justify="center")
        table.add_column("Decision", justify="center")
        table.add_column("WHY Δ", justify="center")

        for result in results:
            decision_color = "green" if result["correct_decision"] else "red"
            decision_icon = "✅" if result["correct_decision"] else "❌"

            table.add_row(
                result["case_name"],
                result["context_quality"].value,
                "Yes" if result["should_enhance"] else "No",
                "Yes" if result["was_enhanced"] else "No",
                f"[{decision_color}]{decision_icon}[/{decision_color}]",
                f"{result['why_improvement']:+.1f}",
            )

        console.print(table)

        # Summary stats
        console.print(
            f"\n[blue]Decision Accuracy: {summary['decision_accuracy']:.1f}%[/blue]"
        )
        console.print(
            f"[blue]Average WHY Improvement: {summary['average_why_improvement']:+.2f}[/blue]"
        )
        console.print(
            f"[green]Good Context Improvement: {summary['good_context_avg_improvement']:+.2f}[/green]"
        )
        console.print(
            f"[red]Bad Context Improvement: {summary['bad_context_avg_improvement']:+.2f}[/red]"
        )


# Usage example:
def main():
    suite = WhyContextBenchmarkSuite()

    # Test enhancement quality
    enhancement_results = suite.run_enhancement_quality_test(
        suite.get_why_context_test_cases()
    )

    overall_passed = enhancement_results["passed"]

    if overall_passed:
        console.print("\n[green]🎉 WHY Context Enhancement is working well![/green]")
    else:
        console.print("\n[red]❌ WHY Context Enhancement needs improvement[/red]")


if __name__ == "__main__":
    main()
