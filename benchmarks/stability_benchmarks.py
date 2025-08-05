"""
Stability Benchmarking Script for DiffMage

This script uses your existing EvaluationBenchmarks class to test evaluation
stability across various real commit examples and scenarios.

Usage:
    python benchmark_stability.py --repo-path /path/to/repo --runs 10
    python benchmark_stability.py --commit-range "HEAD~20..HEAD" --runs 5
    python benchmark_stability.py --test-examples --model gpt-4
    python benchmark_stability.py --batch-test --variance-threshold 0.2
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import git
import random

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box

from diffmage.evaluation.benchmarks import EvaluationBenchmarks, StabilityTestResult
from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator
from diffmage.git.diff_parser import GitDiffParser

console = Console()


class StabilityBenchmarkSuite:
    """Comprehensive stability testing using real commit data"""

    def __init__(self, repo_path: str = ".", model_name: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)
        self.diff_parser = GitDiffParser(repo_path)
        self.evaluator = CommitMessageEvaluator(model_name=model_name)
        self.benchmarks = EvaluationBenchmarks(self.evaluator)
        self.console = console

    def get_real_commit_examples(
        self, commit_range: Optional[str] = None, max_examples: int = 20
    ) -> List[Tuple[str, str, str]]:
        """Extract real commit examples from repository

        Returns:
            List of (commit_hash, commit_message, git_diff) tuples
        """

        if commit_range:
            try:
                commits = list(self.repo.iter_commits(commit_range))
            except Exception as e:
                console.print(
                    f"[red]Error parsing commit range '{commit_range}': {e}[/red]"
                )
                commits = list(self.repo.iter_commits("HEAD", max_count=max_examples))
        else:
            commits = list(self.repo.iter_commits("HEAD", max_count=max_examples))

        examples = []

        console.print(
            f"[blue]Extracting examples from {len(commits)} commits...[/blue]"
        )

        with Progress(console=self.console) as progress:
            task = progress.add_task("Processing commits...", total=len(commits))

            for commit in commits:
                try:
                    message = str(commit.message).strip()

                    if len(commit.parents) > 1 or not message or len(message) < 10:
                        progress.update(task, advance=1)
                        continue

                    git_diff = self.diff_parser.parse_specific_commit(commit.hexsha)

                    if not git_diff or len(git_diff) > 10000:
                        progress.update(task, advance=1)
                        continue

                    examples.append((commit.hexsha, message, git_diff))

                    if len(examples) >= max_examples:
                        break

                except Exception as e:
                    console.print(
                        f"[dim]Warning: Skipped commit {commit.hexsha[:8]}: {e}[/dim]"
                    )

                progress.update(task, advance=1)

        console.print(
            f"[green]Successfully extracted {len(examples)} usable commit examples[/green]"
        )
        return examples

    def get_curated_test_examples(self) -> List[Tuple[str, str, str]]:
        """Get curated test examples with various commit patterns

        Returns:
            List of (example_id, commit_message, git_diff) tuples
        """

        examples = [
            (
                "bug_fix_null_check",
                "fix: resolve null pointer exception in user validation",
                """--- a/src/auth/UserValidator.java
+++ b/src/auth/UserValidator.java
@@ -23,7 +23,7 @@ public class UserValidator {
     }

     public boolean isValidUser(User user) {
-        return user.getEmail().contains("@");
+        return user != null && user.getEmail() != null && user.getEmail().contains("@");
     }
 }""",
            ),
            (
                "feature_dark_mode",
                "feat: implement dark mode toggle in user preferences",
                """--- a/src/components/UserPreferences.jsx
+++ b/src/components/UserPreferences.jsx
@@ -8,6 +8,7 @@ const UserPreferences = () => {
   const [language, setLanguage] = useState('en');
   const [notifications, setNotifications] = useState(true);
+  const [darkMode, setDarkMode] = useState(false);

   const savePreferences = async () => {
     const prefs = {
@@ -15,6 +16,7 @@ const UserPreferences = () => {
       language,
       notifications,
+      darkMode,
     };

     await api.updatePreferences(prefs);
@@ -35,6 +37,13 @@ const UserPreferences = () => {
           onChange={(e) => setNotifications(e.target.checked)}
         />
       </div>
+
+      <div className="preference-item">
+        <label>Dark Mode</label>
+        <input
+          type="checkbox"
+          checked={darkMode}
+          onChange={(e) => setDarkMode(e.target.checked)}
+        />
+      </div>
     </div>
   );""",
            ),
            (
                "refactor_extract_method",
                "refactor: extract user authentication logic into separate service",
                """--- a/src/controllers/AuthController.js
+++ b/src/controllers/AuthController.js
@@ -1,4 +1,5 @@
 const bcrypt = require('bcrypt');
+const AuthService = require('../services/AuthService');

 class AuthController {
   async login(req, res) {
@@ -6,15 +7,7 @@ class AuthController {

     try {
       // Authenticate user
-      const user = await User.findOne({ email });
-      if (!user) {
-        return res.status(401).json({ error: 'Invalid credentials' });
-      }
-
-      const isValidPassword = await bcrypt.compare(password, user.passwordHash);
-      if (!isValidPassword) {
-        return res.status(401).json({ error: 'Invalid credentials' });
-      }
+      const user = await AuthService.authenticateUser(email, password);

       const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET);
       res.json({ token, user: { id: user.id, email: user.email } });
@@ -24,4 +17,22 @@ class AuthController {
   }
 }

+--- /dev/null
++++ b/src/services/AuthService.js
@@ -0,0 +1,22 @@
+const bcrypt = require('bcrypt');
+const User = require('../models/User');
+
+class AuthService {
+  static async authenticateUser(email, password) {
+    const user = await User.findOne({ email });
+    if (!user) {
+      throw new Error('Invalid credentials');
+    }
+
+    const isValidPassword = await bcrypt.compare(password, user.passwordHash);
+    if (!isValidPassword) {
+      throw new Error('Invalid credentials');
+    }
+
+    return user;
+  }
+}
+
+module.exports = AuthService;""",
            ),
            (
                "docs_api_update",
                "docs: update API documentation for user endpoints",
                """--- a/docs/api/users.md
+++ b/docs/api/users.md
@@ -23,6 +23,20 @@ Creates a new user account.
 - `409 Conflict` - Email already exists
 - `500 Internal Server Error` - Server error

+### Request Example
+
+```json
+{
+  "email": "user@example.com",
+  "password": "securePassword123",
+  "firstName": "John",
+  "lastName": "Doe"
+}
+```
+
+### Response Example
+
+```json
 ## GET /api/users/:id

 Retrieves user information by ID.
@@ -35,3 +49,15 @@ Retrieves user information by ID.
 - `200 OK` - User found
 - `404 Not Found` - User not found
 - `500 Internal Server Error` - Server error
+
+### Response Example
+
+```json
+{
+  "id": "123e4567-e89b-12d3-a456-426614174000",
+  "email": "user@example.com",
+  "firstName": "John",
+  "lastName": "Doe",
+  "createdAt": "2024-01-15T10:30:00Z"
+}
+```""",
            ),
            (
                "performance_optimize_query",
                "perf: optimize database query for user search with indexing",
                """--- a/src/models/User.js
+++ b/src/models/User.js
@@ -15,8 +15,12 @@ const userSchema = new mongoose.Schema({
   }
 });

+// Add indexes for better query performance
+userSchema.index({ email: 1 });
+userSchema.index({ firstName: 1, lastName: 1 });
+userSchema.index({ createdAt: -1 });
+
 // Static method for user search
-userSchema.statics.searchUsers = function(searchTerm) {
+userSchema.statics.searchUsers = function(searchTerm, limit = 20) {
   const regex = new RegExp(searchTerm, 'i');
   return this.find({
     $or: [
@@ -24,7 +28,8 @@ userSchema.statics.searchUsers = function(searchTerm) {
       { firstName: regex },
       { lastName: regex }
     ]
-  });
+  })
+  .limit(limit)
+  .sort({ createdAt: -1 });
 };""",
            ),
            (
                "test_add_validation",
                "test: add unit tests for email validation utility",
                """--- /dev/null
+++ b/tests/utils/emailValidator.test.js
@@ -0,0 +1,45 @@
+const { validateEmail } = require('../../src/utils/emailValidator');
+
+describe('Email Validator', () => {
+  describe('valid emails', () => {
+    test('should validate standard email format', () => {
+      expect(validateEmail('user@example.com')).toBe(true);
+      expect(validateEmail('john.doe@company.org')).toBe(true);
+      expect(validateEmail('admin@subdomain.example.co.uk')).toBe(true);
+    });
+
+    test('should validate emails with plus signs', () => {
+      expect(validateEmail('user+tag@example.com')).toBe(true);
+    });
+
+    test('should validate emails with numbers', () => {
+      expect(validateEmail('user123@example123.com')).toBe(true);
+    });
+  });
+
+  describe('invalid emails', () => {
+    test('should reject emails without @ symbol', () => {
+      expect(validateEmail('userexample.com')).toBe(false);
+    });
+
+    test('should reject emails without domain', () => {
+      expect(validateEmail('user@')).toBe(false);
+    });
+
+    test('should reject emails without user part', () => {
+      expect(validateEmail('@example.com')).toBe(false);
+    });
+
+    test('should reject empty strings', () => {
+      expect(validateEmail('')).toBe(false);
+    });
+
+    test('should reject null and undefined', () => {
+      expect(validateEmail(null)).toBe(false);
+      expect(validateEmail(undefined)).toBe(false);
+    });
+  });
+});""",
            ),
        ]

        console.print(f"[green]Loaded {len(examples)} curated test examples[/green]")
        return examples

    def run_single_stability_test(
        self,
        commit_hash: str,
        message: str,
        git_diff: str,
        runs: int = 5,
        variance_threshold: float = 0.3,
    ) -> StabilityTestResult:
        """Run stability test on a single commit example"""

        console.print(f"[blue]Testing stability for: {message[:60]}...[/blue]")
        console.print(
            f"[dim]Commit: {commit_hash[:8] if len(commit_hash) > 8 else commit_hash}[/dim]"
        )

        result = self.benchmarks.stability_test(
            message=message,
            diff=git_diff,
            runs=runs,
            variance_threshold=variance_threshold,
        )

        return result

    def run_batch_stability_test(
        self,
        examples: List[Tuple[str, str, str]],
        runs: int = 5,
        variance_threshold: float = 0.3,
        max_examples: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run stability tests on multiple examples"""

        if max_examples and len(examples) > max_examples:
            examples = random.sample(examples, max_examples)

        console.print(
            f"[blue]Running batch stability test on {len(examples)} examples...[/blue]"
        )
        console.print(
            f"[dim]Runs per example: {runs}, Variance threshold: {variance_threshold}[/dim]"
        )

        results = []
        stable_count = 0
        total_time = 0

        with Progress(console=self.console) as progress:
            task = progress.add_task("Testing stability...", total=len(examples))

            for commit_hash, message, git_diff in examples:
                start_time = time.time()

                try:
                    result = self.benchmarks.stability_test(
                        message=message,
                        diff=git_diff,
                        runs=runs,
                        variance_threshold=variance_threshold,
                    )

                    results.append(result)

                    if result["is_stable"]:  # type: ignore
                        stable_count += 1

                except Exception as e:
                    console.print(f"[red]Error testing {commit_hash[:8]}: {e}[/red]")
                    continue

                total_time += time.time() - start_time
                progress.update(task, advance=1)

        stability_rate = (stable_count / len(results)) * 100 if results else 0
        avg_time_per_test = total_time / len(results) if results else 0

        summary = {
            "total_examples": len(examples),
            "successful_tests": len(results),
            "stable_examples": stable_count,
            "stability_rate": stability_rate,
            "average_time_per_test": avg_time_per_test,
            "total_test_time": total_time,
            "runs_per_example": runs,
            "variance_threshold": variance_threshold,
        }

        self._display_batch_summary(summary)

        return {
            "summary": summary,
            "individual_results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _display_batch_summary(self, summary: Dict[str, Any]):
        """Display batch test summary"""

        console.print(
            Panel(
                f"[bold]Batch Stability Test Results[/bold]\n"
                f"Examples Tested: {summary['successful_tests']}/{summary['total_examples']}\n"
                f"Stable Examples: {summary['stable_examples']}\n"
                f"Stability Rate: {summary['stability_rate']:.1f}%",
                title="📊 Summary",
                border_style="green"
                if summary["stability_rate"] >= 80
                else "yellow"
                if summary["stability_rate"] >= 60
                else "red",
            )
        )

        # Detailed table
        table = Table(title="Performance Metrics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="center")
        table.add_column("Assessment", style="yellow")

        # Stability rate assessment
        if summary["stability_rate"] >= 90:
            stability_assessment = "🟢 Excellent"
        elif summary["stability_rate"] >= 80:
            stability_assessment = "🟡 Good"
        elif summary["stability_rate"] >= 60:
            stability_assessment = "🟠 Acceptable"
        else:
            stability_assessment = "🔴 Needs Improvement"

        # Time assessment
        avg_time = summary["average_time_per_test"]
        if avg_time < 30:
            time_assessment = "🟢 Fast"
        elif avg_time < 60:
            time_assessment = "🟡 Reasonable"
        else:
            time_assessment = "🔴 Slow"

        table.add_row(
            "Stability Rate", f"{summary['stability_rate']:.1f}%", stability_assessment
        )
        table.add_row("Avg Time per Test", f"{avg_time:.1f}s", time_assessment)
        table.add_row("Total Test Time", f"{summary['total_test_time']:.1f}s", "")
        table.add_row("Runs per Example", str(summary["runs_per_example"]), "")
        table.add_row("Variance Threshold", str(summary["variance_threshold"]), "")

        console.print(table)

    def run_comparative_stability_test(
        self, examples: List[Tuple[str, str, str]], models: List[str], runs: int = 3
    ) -> Dict[str, Any]:
        """Compare stability across different models"""

        console.print(
            f"[blue]Running comparative stability test across {len(models)} models...[/blue]"
        )

        model_results = {}

        for model in models:
            console.print(f"[yellow]Testing model: {model}[/yellow]")

            # Create new evaluator for this model
            evaluator = CommitMessageEvaluator(model_name=model)
            benchmarks = EvaluationBenchmarks(evaluator)

            model_stability_results = []

            for i, (commit_hash, message, git_diff) in enumerate(
                examples[:5]
            ):  # Limit for comparative test
                try:
                    result = benchmarks.stability_test(
                        message=message,
                        diff=git_diff,
                        runs=runs,
                        variance_threshold=0.3,
                    )

                    model_stability_results.append(
                        {
                            "example_id": i,
                            "is_stable": result["is_stable"],
                            "max_variance": result["max_variance"],
                            "commit_hash": commit_hash,
                        }
                    )

                except Exception as e:
                    console.print(
                        f"[red]Error with {model} on {commit_hash[:8]}: {e}[/red]"
                    )
                    continue

            model_results[model] = model_stability_results

        # Calculate comparative statistics
        comparative_stats = self._calculate_comparative_stats(model_results)
        self._display_comparative_results(comparative_stats)

        return {
            "model_results": model_results,
            "comparative_stats": comparative_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_comparative_stats(
        self, model_results: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate comparative statistics across models"""

        stats = {}

        for model, results in model_results.items():
            if not results:
                continue

            stable_count = sum(1 for r in results if r["is_stable"])
            total_count = len(results)
            avg_variance = (
                sum(r["max_variance"] for r in results) / total_count
                if total_count > 0
                else 0
            )

            stats[model] = {
                "stability_rate": (stable_count / total_count * 100)
                if total_count > 0
                else 0,
                "average_variance": avg_variance,
                "stable_examples": stable_count,
                "total_examples": total_count,
            }

        return stats

    def _display_comparative_results(self, stats: Dict[str, Any]):
        """Display comparative model results"""

        table = Table(title="Model Stability Comparison", box=box.SIMPLE)
        table.add_column("Model", style="cyan")
        table.add_column("Stability Rate", justify="center")
        table.add_column("Avg Variance", justify="center")
        table.add_column("Stable/Total", justify="center")
        table.add_column("Assessment", style="yellow")

        for model, model_stats in stats.items():
            rate = model_stats["stability_rate"]

            if rate >= 80:
                assessment = "🟢 Excellent"
            elif rate >= 60:
                assessment = "🟡 Good"
            else:
                assessment = "🔴 Needs Work"

            table.add_row(
                model,
                f"{rate:.1f}%",
                f"{model_stats['average_variance']:.3f}",
                f"{model_stats['stable_examples']}/{model_stats['total_examples']}",
                assessment,
            )

        console.print(table)


def main():
    """Main CLI interface"""

    parser = argparse.ArgumentParser(
        description="Stability Benchmarking Script for DiffMage"
    )
    parser.add_argument("--repo-path", default=".", help="Path to git repository")
    parser.add_argument("--model", help="AI model to test (default: uses your default)")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per test")
    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=0.3,
        help="Variance threshold for stability",
    )

    # Test data options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--commit-range", help="Git commit range (e.g., HEAD~10..HEAD)")
    group.add_argument(
        "--test-examples", action="store_true", help="Use curated test examples"
    )
    group.add_argument("--single-commit", help="Test single commit by hash")

    # Test options
    parser.add_argument(
        "--batch-test", action="store_true", help="Run batch stability test"
    )
    parser.add_argument("--comparative-test", help="Compare models (comma-separated)")
    parser.add_argument(
        "--max-examples", type=int, default=10, help="Maximum examples to test"
    )
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    try:
        suite = StabilityBenchmarkSuite(args.repo_path, args.model)
    except Exception as e:
        console.print(f"[red]Error initializing benchmark suite: {e}[/red]")
        return 1

    results = None

    try:
        if args.single_commit:
            # Test single commit
            commits = list(suite.repo.iter_commits(args.single_commit, max_count=1))
            if not commits:
                console.print(f"[red]Commit not found: {args.single_commit}[/red]")
                return 1

            commit = commits[0]
            message = str(commit.message).strip()
            git_diff = suite.diff_parser.parse_specific_commit(commit.hexsha)[1]

            results = suite.run_single_stability_test(
                commit.hexsha, message, git_diff, args.runs, args.variance_threshold
            )

        elif args.test_examples:
            # Use curated examples
            examples = suite.get_curated_test_examples()

            if args.comparative_test:
                models = [m.strip() for m in args.comparative_test.split(",")]
                results = suite.run_comparative_stability_test(
                    examples, models, args.runs
                )
            elif args.batch_test:
                results = suite.run_batch_stability_test(
                    examples, args.runs, args.variance_threshold, args.max_examples
                )
            else:
                # Test first example
                commit_hash, message, git_diff = examples[0]
                results = suite.run_single_stability_test(
                    commit_hash, message, git_diff, args.runs, args.variance_threshold
                )

        else:
            # Use real repository commits
            examples = suite.get_real_commit_examples(
                args.commit_range, args.max_examples
            )

            if not examples:
                console.print("[red]No suitable commit examples found[/red]")
                return 1

            if args.comparative_test:
                models = [m.strip() for m in args.comparative_test.split(",")]
                results = suite.run_comparative_stability_test(
                    examples, models, args.runs
                )
            elif args.batch_test:
                results = suite.run_batch_stability_test(
                    examples, args.runs, args.variance_threshold, args.max_examples
                )
            else:
                # Test first example
                commit_hash, message, git_diff = examples[0]
                results = suite.run_single_stability_test(
                    commit_hash, message, git_diff, args.runs, args.variance_threshold
                )

        # Save results if requested
        if args.output and results:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"[green]Results saved to {args.output}[/green]")

        console.print("\n[green]Benchmarking completed successfully! ✅[/green]")

    except Exception as e:
        console.print(f"[red]Error during benchmarking: {e}[/red]")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
