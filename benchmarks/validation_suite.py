"""
Evaluation *Smoke Test* Validation Suite for DiffMage

This script performs fundamental sanity checks on your LLM evaluator to ensure
it's working correctly before running extensive benchmarks.

Usage:
    python validation_suite.py --all
    python validation_suite.py --test obvious-cases
    python validation_suite.py --test ranking-consistency
    python validation_suite.py --test score-distribution
    python validation_suite.py --test edge-cases
"""

import argparse
import statistics
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box

try:
    from diffmage.evaluation.commit_message_evaluator import CommitMessageEvaluator
except ImportError as e:
    print(f"Error importing DiffMage modules: {e}")
    print("Make sure you're running from the project root and the package is installed")
    exit(1)

console = Console()


@dataclass
class ValidationCase:
    """A test case for validation"""

    name: str
    commit_message: str
    git_diff: str
    expected_score_range: Tuple[float, float]  # (min, max)
    expected_quality: str  # "excellent", "good", "average", "poor", "very_poor"
    description: str


class EvaluationValidator:
    """Validates that the LLM evaluator is working correctly"""

    def __init__(self, model_name: Optional[str] = None):
        self.evaluator = CommitMessageEvaluator(model_name=model_name)
        self.console = console

    def get_obvious_test_cases(self) -> List[ValidationCase]:
        """Get test cases with obvious expected outcomes"""

        return [
            # EXCELLENT cases (4.5-5.0)
            ValidationCase(
                name="excellent_security_with_impact",
                commit_message="fix: resolve authentication bypass allowing unauthorized admin access\n\nCritical security vulnerability discovered in production where users could escalate privileges by manipulating JWT tokens. Affecting ~2,300 enterprise customers with potential for full system compromise.\n\n The root cause is a missing signature verification in token validation middleware. Impact: Complete authentication bypass, unauthorized admin panel access\nSolution: Implement proper HMAC signature validation with key rotation\nTesting: Verified with penetration testing and security audit\n\nResolves: SEC-2024-001, addresses compliance requirements for SOC2 certification.",
                git_diff="""--- a/src/middleware/auth.py
                +++ b/src/middleware/auth.py
                @@ -1,4 +1,5 @@
                import jwt
                +import hmac
                +import hashlib
                from flask import request, jsonify

                def verify_token(token):
                    try:
                -        payload = jwt.decode(token, verify=False)
                +        # Verify signature with rotating keys
                +        payload = jwt.decode(token, get_current_secret_key(), algorithms=['HS256'])
                +
                +        # Additional signature verification
                +        expected_sig = hmac.new(
                +            get_signing_key().encode(),
                +            f"{payload['user_id']}{payload['exp']}".encode(),
                +            hashlib.sha256
                +        ).hexdigest()
                +
                +        if not hmac.compare_digest(payload.get('sig', ''), expected_sig):
                +            raise jwt.InvalidTokenError("Invalid signature")
                +
                        return payload
                    except jwt.InvalidTokenError:
                        return None""",
                expected_score_range=(4.5, 5.0),
                expected_quality="excellent",
                description="Security fix with clear business impact, root cause analysis, and comprehensive solution",
            ),
            ValidationCase(
                name="excellent_performance_with_metrics",
                commit_message="perf: optimize user search query reducing response time from 8s to 200ms\n\nUser search was causing timeouts and abandonment during peak hours. Analysis showed 47% of users abandoned search after 5+ second wait times, directly impacting conversion rates.\n\nProblem: Sequential database queries without indexing on 2M+ user records\nMetrics: 8-12 second response times, 47% abandonment rate, 200+ timeout errors/day\nSolution: Implement composite indexes + query optimization + result pagination\nResults: 200ms average response time, 12% abandonment rate, zero timeouts\n\nA/B testing shows 23% increase in search completion rates.\nEstimated impact: +$180K quarterly revenue from improved user engagement.",
                git_diff="""--- a/src/models/User.js
            +++ b/src/models/User.js
            @@ -10,15 +10,25 @@ const userSchema = new mongoose.Schema({
            updatedAt: { type: Date, default: Date.now }
            });

            +// Composite indexes for optimized search
            +userSchema.index({
            +  firstName: 'text',
            +  lastName: 'text',
            +  email: 'text'
            +}, {
            +  weights: { firstName: 10, lastName: 5, email: 1 }
            +});
            +userSchema.index({ createdAt: -1 });
            +userSchema.index({ email: 1 }, { unique: true });

            // Optimized search with pagination and relevance scoring
            -userSchema.statics.searchUsers = function(searchTerm) {
            +userSchema.statics.searchUsers = function(searchTerm, page = 1, limit = 20) {
            const regex = new RegExp(searchTerm, 'i');
            -  return this.find({
            +
            +  return this.find({
                $or: [
            -      { email: regex },
            -      { firstName: regex },
            -      { lastName: regex }
            +      { $text: { $search: searchTerm } },
            +      { email: regex }
                ]
            -  });
            +  }, { score: { $meta: 'textScore' } })
            +    .sort({ score: { $meta: 'textScore' }, createdAt: -1 })
            +    .limit(limit)
            +    .skip((page - 1) * limit);
            };""",
                expected_score_range=(4.5, 5.0),
                expected_quality="excellent",
                description="Performance optimization with detailed metrics, business impact, and quantified results",
            ),
            # GOOD cases (3.5-4.4)
            ValidationCase(
                name="security_fix",
                commit_message="fix: resolve critical SQL injection vulnerability in user authentication",
                git_diff="""--- a/src/auth/UserAuth.py
                +++ b/src/auth/UserAuth.py
                @@ -23,7 +23,8 @@ class UserAuth:
                    def authenticate_user(self, username, password):
                -        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
                +        query = "SELECT * FROM users WHERE username=? AND password=?"
                +        return self.db.execute(query, (username, password))
                -        return self.db.execute(query)""",
                expected_score_range=(3.5, 4.4),
                expected_quality="good",
                description="Clear security fix with good explanation",
            ),
            ValidationCase(
                name="feature_with_context",
                commit_message="feat: implement user password reset with email verification\n\nAdds secure password reset flow:\n- Generate time-limited reset tokens\n- Send verification emails\n- Validate tokens before allowing reset\n- Log security events for auditing",
                git_diff="""--- a/src/auth/PasswordReset.py
                +++ b/src/auth/PasswordReset.py
                @@ -0,0 +1,45 @@
                +import secrets
                +import hashlib
                +from datetime import datetime, timedelta
                +
                +class PasswordReset:
                +    def __init__(self, email_service, user_service):
                +        self.email_service = email_service
                +        self.user_service = user_service
                +
                +    def request_reset(self, email):
                +        user = self.user_service.find_by_email(email)
                +        if not user:
                +            return False  # Don't reveal if email exists
                +
                +        token = secrets.token_urlsafe(32)
                +        expires_at = datetime.now() + timedelta(hours=1)
                +
                +        self.user_service.store_reset_token(user.id, token, expires_at)
                +        self.email_service.send_reset_email(email, token)
                +
                +        return True""",
                expected_score_range=(3.5, 4.4),
                expected_quality="good",
                description="Comprehensive feature with detailed explanation",
            ),
            ValidationCase(
                name="simple_bug_fix",
                commit_message="fix: handle null values in user profile display",
                git_diff="""--- a/src/components/UserProfile.jsx
                +++ b/src/components/UserProfile.jsx
                @@ -15,7 +15,7 @@ const UserProfile = ({ user }) => {
                    <div className="profile-container">
                    <h2>{user.name}</h2>
                -      <p>Email: {user.email}</p>
                +      <p>Email: {user.email || 'Not provided'}</p>
                -      <p>Bio: {user.bio}</p>
                +      <p>Bio: {user.bio || 'No bio available'}</p>
                    </div>
                );""",
                expected_score_range=(3.5, 4.4),
                expected_quality="good",
                description="Clear bug fix, could use more detail",
            ),
            # AVERAGE cases (2.5-3.4)
            ValidationCase(
                name="average_refactor",
                commit_message="refactor: move validation logic to separate service",
                git_diff="""--- a/src/controllers/UserController.js
        +++ b/src/controllers/UserController.js
        @@ -5,12 +5,7 @@ class UserController {
        async createUser(userData) {
            try {
        -      // Validate email format
        -      if (!userData.email || !userData.email.includes('@')) {
        -        throw new Error('Invalid email');
        -      }
        -      // Validate required fields
        -      if (!userData.firstName || !userData.lastName) {
        -        throw new Error('Missing required fields');
        -      }
        +      ValidationService.validateUserData(userData);

            const user = await User.create(userData);
            return { success: true, user };
        @@ -18,4 +13,17 @@ class UserController {
            return { success: false, error: error.message };
            }
        }
        +}
        +
        +--- /dev/null
        ++++ b/src/services/ValidationService.js
        @@ -0,0 +1,15 @@
        +class ValidationService {
        +  static validateUserData(userData) {
        +    if (!userData.email || !userData.email.includes('@')) {
        +      throw new Error('Invalid email');
        +    }
        +
        +    if (!userData.firstName || !userData.lastName) {
        +      throw new Error('Missing required fields');
        +    }
        +  }
        }""",
                expected_score_range=(2.5, 3.4),
                expected_quality="average",
                description="Basic refactor, describes what but minimal why context",
            ),
            ValidationCase(
                name="average_bug_fix",
                commit_message="fix: prevent crash when user profile is empty",
                git_diff="""--- a/src/components/UserProfile.jsx
        +++ b/src/components/UserProfile.jsx
        @@ -8,7 +8,7 @@ const UserProfile = ({ user }) => {
        return (
            <div className="profile-container">
            <h2>{user.name}</h2>
        -      <p>Bio: {user.bio}</p>
        +      <p>Bio: {user.bio || 'No bio provided'}</p>
        -      <p>Joined: {new Date(user.joinedAt).toLocaleDateString()}</p>
        +      <p>Joined: {user.joinedAt ? new Date(user.joinedAt).toLocaleDateString() : 'Unknown'}</p>
            </div>
        );
        };""",
                expected_score_range=(2.5, 3.4),
                expected_quality="average",
                description="Fixes the issue but doesn't explain impact or root cause",
            ),
            ValidationCase(
                name="average_feature_basic",
                commit_message="feat: add dark mode toggle to settings page\n\n- Add toggle switch component\n- Store preference in localStorage\n- Apply theme on page load",
                git_diff="""--- a/src/pages/Settings.jsx
        +++ b/src/pages/Settings.jsx
        @@ -1,4 +1,5 @@
        import React, { useState } from 'react';
        +import ToggleSwitch from '../components/ToggleSwitch';

        const Settings = () => {
        const [notifications, setNotifications] = useState(true);
        +  const [darkMode, setDarkMode] = useState(
        +    localStorage.getItem('darkMode') === 'true'
        +  );

        +  const handleDarkModeToggle = (enabled) => {
        +    setDarkMode(enabled);
        +    localStorage.setItem('darkMode', enabled);
        +    document.body.classList.toggle('dark-mode', enabled);
        +  };

        return (
            <div className="settings-page">
            <h1>Settings</h1>

            <div className="setting-item">
                <label>Enable Notifications</label>
                <ToggleSwitch
                checked={notifications}
                onChange={setNotifications}
                />
            </div>

        +      <div className="setting-item">
        +        <label>Dark Mode</label>
        +        <ToggleSwitch
        +          checked={darkMode}
        +          onChange={handleDarkModeToggle}
        +        />
        +      </div>
            </div>
        );
        };""",
                expected_score_range=(2.5, 3.4),
                expected_quality="average",
                description="Describes the feature clearly but lacks user motivation or business context",
            ),
            ValidationCase(
                name="average_docs_update",
                commit_message="docs: update installation instructions for new deployment process",
                git_diff="""--- a/README.md
        +++ b/README.md
        @@ -15,8 +15,12 @@ A modern web application for managing user accounts.

        ## Installation

        -1. Clone the repository
        -2. Run `npm install`
        -3. Start with `npm start`
        +1. Clone the repository: `git clone https://github.com/company/app.git`
        +2. Install dependencies: `npm install`
        +3. Copy environment file: `cp .env.example .env`
        +4. Configure your database settings in `.env`
        +5. Run database migrations: `npm run migrate`
        +6. Start the application: `npm start`

        ## Configuration
        @@ -25,4 +29,8 @@ A modern web application for managing user accounts.

        - `DATABASE_URL` - Your database connection string
        - `JWT_SECRET` - Secret key for JWT tokens
        +- `SMTP_HOST` - Email server host
        +- `SMTP_PORT` - Email server port
        +- `SMTP_USER` - Email username
        +- `SMTP_PASS` - Email password""",
                expected_score_range=(2.5, 3.4),
                expected_quality="average",
                description="Updates documentation but doesn't explain why changes were needed",
            ),
            # POOR cases (1.5-2.4)
            ValidationCase(
                name="generic_update",
                commit_message="update user component",
                git_diff="""--- a/src/components/User.jsx
                +++ b/src/components/User.jsx
                @@ -10,6 +10,7 @@ const User = ({ userData }) => {
                return (
                    <div className="user">
                    <span>{userData.name}</span>
                +      <span>{userData.role}</span>
                    </div>
                );""",
                expected_score_range=(1.5, 2.4),
                expected_quality="poor",
                description="Vague message, minimal change",
            ),
            ValidationCase(
                name="meaningless_message",
                commit_message="fix stuff",
                git_diff="""--- a/src/utils/helper.js
+++ b/src/utils/helper.js
@@ -5,7 +5,7 @@ function processData(data) {
   if (!data) {
     return null;
   }
-  return data.map(item => item.value);
+  return data.map(item => item.value || 0);
 }""",
                expected_score_range=(1.5, 2.4),
                expected_quality="poor",
                description="Meaningless commit message",
            ),
            # VERY POOR cases (1.0-1.4)
            ValidationCase(
                name="gibberish",
                commit_message="asdf jkl; qwerty",
                git_diff="""--- a/src/test.js
+++ b/src/test.js
@@ -1,3 +1,4 @@
 // Test file
 console.log('hello');
+console.log('world');""",
                expected_score_range=(1.0, 1.4),
                expected_quality="very_poor",
                description="Nonsensical commit message",
            ),
        ]

    def get_edge_test_cases(self) -> List[ValidationCase]:
        """Get edge cases that might break the evaluator"""

        return [
            ValidationCase(
                name="empty_message",
                commit_message="",
                git_diff="--- a/file.txt\n+++ b/file.txt\n@@ -1 +1,2 @@\n hello\n+world",
                expected_score_range=(1.0, 1.4),
                expected_quality="very_poor",
                description="Empty commit message",
            ),
            ValidationCase(
                name="very_long_message",
                commit_message="fix: "
                + "very " * 100
                + "long commit message that goes on and on and provides way too much detail about a simple change "
                * 10,
                git_diff="--- a/file.txt\n+++ b/file.txt\n@@ -1 +1,2 @@\n hello\n+world",
                expected_score_range=(1.0, 1.4),
                expected_quality="poor",
                description="Excessively long commit message",
            ),
            ValidationCase(
                name="special_characters",
                commit_message="fix: handle émojis 🚀 and ñoñ-ASCII çharacters in üser input",
                git_diff="""--- a/src/input.py
+++ b/src/input.py
@@ -1,3 +1,4 @@
 def process_input(text):
+    text = text.encode('utf-8').decode('utf-8')
     return text.strip()""",
                expected_score_range=(3.5, 4.4),
                expected_quality="good",
                description="Special characters and emojis",
            ),
            ValidationCase(
                name="no_diff",
                commit_message="fix: important bug fix",
                git_diff="",
                expected_score_range=(1.0, 2.4),
                expected_quality="poor",
                description="No diff provided",
            ),
            ValidationCase(
                name="merge_commit",
                commit_message="Merge branch 'feature/user-auth' into main",
                git_diff="""--- a/src/auth.py
+++ b/src/auth.py
@@ -1,10 +1,20 @@
 # Auth module
+# New authentication features

 def login(user, password):
     return validate_credentials(user, password)
+
+def logout(user):
+    clear_session(user)
+
+def reset_password(email):
+    send_reset_email(email)""",
                expected_score_range=(1.0, 2.4),
                expected_quality="poor",
                description="Merge commit (usually auto-generated)",
            ),
        ]

    def test_obvious_cases(self) -> Dict[str, Any]:
        """Test if evaluator handles obviously good/bad cases correctly"""

        console.print(
            Panel(
                "[bold]Testing Obvious Cases[/bold]\n"
                "Evaluator should clearly distinguish between excellent and poor commit messages",
                title="🎯 Obvious Cases Test",
                border_style="blue",
            )
        )

        test_cases = self.get_obvious_test_cases()
        results = []

        with Progress(console=self.console) as progress:
            task = progress.add_task(
                "Evaluating obvious cases...", total=len(test_cases)
            )

            for case in test_cases:
                try:
                    result = self.evaluator.evaluate_commit_message(
                        case.commit_message, case.git_diff
                    )

                    # Check if score is in expected range
                    in_range = (
                        case.expected_score_range[0]
                        <= result.overall_score
                        <= case.expected_score_range[1]
                    )

                    results.append(
                        {
                            "case": case,
                            "result": result,
                            "in_expected_range": in_range,
                            "score_deviation": self._calculate_deviation(
                                result.overall_score, case.expected_score_range
                            ),
                        }
                    )

                except Exception as e:
                    console.print(f"[red]Error evaluating {case.name}: {e}[/red]")
                    results.append(
                        {
                            "case": case,
                            "result": None,
                            "error": str(e),
                            "in_expected_range": False,
                            "score_deviation": float("inf"),
                        }
                    )

                progress.update(task, advance=1)

        # Analyze results
        success_rate = (
            sum(1 for r in results if r.get("in_expected_range", False))
            / len(results)
            * 100
        )
        avg_deviation = statistics.mean(
            [
                r["score_deviation"]
                for r in results
                if r["score_deviation"] != float("inf")
            ]
        )

        # Display results
        self._display_obvious_cases_results(results, success_rate, avg_deviation)

        return {
            "test_name": "obvious_cases",
            "success_rate": success_rate,
            "average_deviation": avg_deviation,
            "results": results,
            "passed": success_rate >= 70,  # 70% of obvious cases should be correct
        }

    def test_ranking_consistency(self) -> Dict[str, Any]:
        """Test if evaluator consistently ranks messages in logical order"""

        console.print(
            Panel(
                "[bold]Testing Ranking Consistency[/bold]\n"
                "Evaluator should rank obviously better messages higher than worse ones",
                title="📊 Ranking Test",
                border_style="green",
            )
        )

        # Get subset of test cases for ranking
        test_cases = self.get_obvious_test_cases()

        # Sort by expected quality for comparison
        expected_order = sorted(
            test_cases, key=lambda x: x.expected_score_range[1], reverse=True
        )

        # Evaluate all cases
        evaluated_cases = []

        with Progress(console=self.console) as progress:
            task = progress.add_task("Evaluating for ranking...", total=len(test_cases))

            for case in test_cases:
                try:
                    result = self.evaluator.evaluate_commit_message(
                        case.commit_message, case.git_diff
                    )
                    evaluated_cases.append((case, result))
                except Exception as e:
                    console.print(f"[red]Error evaluating {case.name}: {e}[/red]")
                    continue

                progress.update(task, advance=1)

        # Sort by actual scores
        actual_order = sorted(
            evaluated_cases, key=lambda x: x[1].overall_score, reverse=True
        )

        # Calculate ranking consistency
        ranking_violations = self._count_ranking_violations(
            expected_order, actual_order
        )
        total_pairs = len(evaluated_cases) * (len(evaluated_cases) - 1) // 2
        consistency_rate = (
            (total_pairs - ranking_violations) / total_pairs * 100
            if total_pairs > 0
            else 0
        )

        # Display results
        self._display_ranking_results(
            expected_order, actual_order, consistency_rate, ranking_violations
        )

        return {
            "test_name": "ranking_consistency",
            "consistency_rate": consistency_rate,
            "ranking_violations": ranking_violations,
            "total_pairs": total_pairs,
            "passed": consistency_rate >= 80,  # 80% of rankings should be consistent
        }

    def test_score_distribution(self) -> Dict[str, Any]:
        """Test if evaluator uses the full score range appropriately"""

        console.print(
            Panel(
                "[bold]Testing Score Distribution[/bold]\n"
                "Evaluator should use the full 1-5 scale and not cluster around one value",
                title="📈 Distribution Test",
                border_style="yellow",
            )
        )

        all_cases = self.get_obvious_test_cases() + self.get_edge_test_cases()
        scores = []

        with Progress(console=self.console) as progress:
            task = progress.add_task("Collecting scores...", total=len(all_cases))

            for case in all_cases:
                try:
                    result = self.evaluator.evaluate_commit_message(
                        case.commit_message, case.git_diff
                    )
                    scores.append(
                        {
                            "case_name": case.name,
                            "overall_score": result.overall_score,
                            "what_score": result.what_score,
                            "why_score": result.why_score,
                            "expected_quality": case.expected_quality,
                        }
                    )
                except Exception as e:
                    console.print(f"[red]Error evaluating {case.name}: {e}[/red]")
                    continue

                progress.update(task, advance=1)

        if not scores:
            return {
                "test_name": "score_distribution",
                "passed": False,
                "error": "No scores collected",
            }

        # Analyze distribution
        overall_scores = [s["overall_score"] for s in scores]
        distribution_stats = {
            "mean": statistics.mean(overall_scores),
            "median": statistics.median(overall_scores),
            "std_dev": statistics.stdev(overall_scores)
            if len(overall_scores) > 1
            else 0,
            "min": min(overall_scores),
            "max": max(overall_scores),
            "range": max(overall_scores) - min(overall_scores),
        }

        # Check for problems
        problems = []
        if distribution_stats["std_dev"] < 0.5:
            problems.append("Low variance - scores too clustered")
        if distribution_stats["range"] < 2.0:
            problems.append("Narrow range - not using full scale")
        if distribution_stats["mean"] > 4.0:
            problems.append("Grade inflation - scores too high")
        if distribution_stats["mean"] < 2.0:
            problems.append("Grade deflation - scores too low")

        # Display results
        self._display_distribution_results(distribution_stats, scores, problems)

        return {
            "test_name": "score_distribution",
            "distribution_stats": distribution_stats,
            "problems": problems,
            "scores": scores,
            "passed": len(problems) == 0,
        }

    def test_edge_cases(self) -> Dict[str, Any]:
        """Test if evaluator handles edge cases gracefully"""

        console.print(
            Panel(
                "[bold]Testing Edge Cases[/bold]\n"
                "Evaluator should handle unusual inputs without crashing",
                title="⚠️ Edge Cases Test",
                border_style="red",
            )
        )

        edge_cases = self.get_edge_test_cases()
        results = []

        with Progress(console=self.console) as progress:
            task = progress.add_task("Testing edge cases...", total=len(edge_cases))

            for case in edge_cases:
                try:
                    result = self.evaluator.evaluate_commit_message(
                        case.commit_message, case.git_diff
                    )

                    # Check if result is reasonable
                    is_reasonable = (
                        1.0 <= result.overall_score <= 5.0
                        and 1.0 <= result.what_score <= 5.0
                        and 1.0 <= result.why_score <= 5.0
                        and result.reasoning
                        and len(result.reasoning) > 10
                    )

                    results.append(
                        {
                            "case": case,
                            "result": result,
                            "handled_gracefully": True,
                            "is_reasonable": is_reasonable,
                            "error": None,
                        }
                    )

                except Exception as e:
                    results.append(
                        {
                            "case": case,
                            "result": None,
                            "handled_gracefully": False,
                            "is_reasonable": False,
                            "error": str(e),
                        }
                    )

                progress.update(task, advance=1)

        # Analyze results
        graceful_handling_rate = (
            sum(1 for r in results if r["handled_gracefully"]) / len(results) * 100
        )
        reasonable_results_rate = (
            sum(1 for r in results if r.get("is_reasonable", False))
            / len(results)
            * 100
        )

        # Display results
        self._display_edge_cases_results(
            results, graceful_handling_rate, reasonable_results_rate
        )

        return {
            "test_name": "edge_cases",
            "graceful_handling_rate": graceful_handling_rate,
            "reasonable_results_rate": reasonable_results_rate,
            "results": results,
            "passed": graceful_handling_rate >= 90 and reasonable_results_rate >= 70,
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""

        console.print(
            Panel(
                "[bold]Running Complete Validation Suite[/bold]\n"
                "Testing fundamental evaluator functionality",
                title="🧪 Validation Suite",
                border_style="cyan",
            )
        )

        all_results = {}

        # Run each test
        tests = [
            ("obvious_cases", self.test_obvious_cases),
            ("ranking_consistency", self.test_ranking_consistency),
            ("score_distribution", self.test_score_distribution),
            ("edge_cases", self.test_edge_cases),
        ]

        for test_name, test_func in tests:
            console.print(
                f"\n[blue]Running {test_name.replace('_', ' ').title()} test...[/blue]"
            )
            try:
                all_results[test_name] = test_func()
            except Exception as e:
                console.print(f"[red]Test {test_name} failed with error: {e}[/red]")
                all_results[test_name] = {
                    "test_name": test_name,
                    "passed": False,
                    "error": str(e),
                }

        # Overall assessment
        passed_tests = sum(
            1 for result in all_results.values() if result.get("passed", False)
        )
        total_tests = len(all_results)
        overall_pass_rate = passed_tests / total_tests * 100
        model_used: str = self.evaluator.model_name

        # Display summary
        self._display_overall_summary(all_results, overall_pass_rate)

        return {
            "overall_pass_rate": overall_pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "model_used": model_used,
            "individual_results": all_results,
            "evaluator_ready": overall_pass_rate >= 75,  # 75% of tests should pass
        }

    # Helper methods for calculations and display
    def _calculate_deviation(
        self, actual_score: float, expected_range: Tuple[float, float]
    ) -> float:
        """Calculate how far actual score is from expected range"""
        if expected_range[0] <= actual_score <= expected_range[1]:
            return 0.0
        elif actual_score < expected_range[0]:
            return expected_range[0] - actual_score
        else:
            return actual_score - expected_range[1]

    def _count_ranking_violations(
        self, expected_order: List, actual_order: List
    ) -> int:
        """Count pairs that are ranked in wrong order"""
        violations = 0
        actual_scores = {
            case.name: score
            for case, score in [(c, r.overall_score) for c, r in actual_order]
        }

        for i, case1 in enumerate(expected_order):
            for case2 in expected_order[i + 1 :]:
                # case1 should score higher than case2
                if actual_scores.get(case1.name, 0) < actual_scores.get(case2.name, 0):
                    violations += 1

        return violations

    def _display_obvious_cases_results(
        self, results: List, success_rate: float, avg_deviation: float
    ):
        """Display obvious cases test results"""

        table = Table(title="Obvious Cases Results", box=box.SIMPLE)
        table.add_column("Case", style="cyan")
        table.add_column("Expected", justify="center")
        table.add_column("Actual", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Deviation", justify="center")

        for r in results:
            if r.get("result"):
                status = "✅ Pass" if r["in_expected_range"] else "❌ Fail"
                status_color = "green" if r["in_expected_range"] else "red"

                expected_range = f"{r['case'].expected_score_range[0]:.1f}-{r['case'].expected_score_range[1]:.1f}"
                actual_score = f"{r['result'].overall_score:.1f}"
                deviation = f"{r['score_deviation']:.1f}"

                table.add_row(
                    r["case"].name,
                    expected_range,
                    actual_score,
                    f"[{status_color}]{status}[/{status_color}]",
                    deviation,
                )
            else:
                table.add_row(
                    r["case"].name, "N/A", "ERROR", "[red]❌ Error[/red]", "∞"
                )

        console.print(table)

        # Summary
        summary_color = (
            "green" if success_rate >= 70 else "yellow" if success_rate >= 50 else "red"
        )
        console.print(
            f"\n[{summary_color}]Success Rate: {success_rate:.1f}% | Average Deviation: {avg_deviation:.2f}[/{summary_color}]"
        )

    def _display_ranking_results(
        self,
        expected_order: List,
        actual_order: List,
        consistency_rate: float,
        violations: int,
    ):
        """Display ranking consistency results"""

        table = Table(title="Ranking Comparison", box=box.SIMPLE)
        table.add_column("Rank", justify="center")
        table.add_column("Expected", style="cyan")
        table.add_column("Actual", style="yellow")
        table.add_column("Score", justify="center")

        for i, (case, result) in enumerate(actual_order[:5]):  # Show top 5
            expected_case = expected_order[i] if i < len(expected_order) else None
            expected_name = expected_case.name if expected_case else "N/A"

            table.add_row(
                str(i + 1), expected_name, case.name, f"{result.overall_score:.1f}"
            )

        console.print(table)

        # Summary
        summary_color = (
            "green"
            if consistency_rate >= 80
            else "yellow"
            if consistency_rate >= 60
            else "red"
        )
        console.print(
            f"\n[{summary_color}]Ranking Consistency: {consistency_rate:.1f}% | Violations: {violations}[/{summary_color}]"
        )

    def _display_distribution_results(self, stats: Dict, scores: List, problems: List):
        """Display score distribution results"""

        table = Table(title="Score Distribution Statistics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="center")
        table.add_column("Assessment", style="yellow")

        table.add_row(
            "Mean",
            f"{stats['mean']:.2f}",
            "Good" if 2.5 <= stats["mean"] <= 3.5 else "Check",
        )
        table.add_row(
            "Std Dev",
            f"{stats['std_dev']:.2f}",
            "Good" if stats["std_dev"] >= 0.5 else "Low variance",
        )
        table.add_row(
            "Range",
            f"{stats['range']:.2f}",
            "Good" if stats["range"] >= 2.0 else "Narrow range",
        )
        table.add_row("Min", f"{stats['min']:.2f}", "")
        table.add_row("Max", f"{stats['max']:.2f}", "")

        console.print(table)

        if problems:
            console.print("\n[red]Issues Found:[/red]")
            for problem in problems:
                console.print(f"  • {problem}")
        else:
            console.print("\n[green]✅ Score distribution looks healthy[/green]")

    def _display_edge_cases_results(
        self, results: List, graceful_rate: float, reasonable_rate: float
    ):
        """Display edge cases test results"""

        table = Table(title="Edge Cases Results", box=box.SIMPLE)
        table.add_column("Case", style="cyan")
        table.add_column("Handled", justify="center")
        table.add_column("Reasonable", justify="center")
        table.add_column("Error", style="red")

        for r in results:
            handled = "✅ Yes" if r["handled_gracefully"] else "❌ No"
            reasonable = "✅ Yes" if r.get("is_reasonable", False) else "❌ No"
            error = (
                r.get("error", "")[:50] + "..."
                if r.get("error") and len(r.get("error", "")) > 50
                else r.get("error", "")
            )

            table.add_row(r["case"].name, handled, reasonable, error)

        console.print(table)

        console.print(
            f"\n[blue]Graceful Handling: {graceful_rate:.1f}% | Reasonable Results: {reasonable_rate:.1f}%[/blue]"
        )

    def _display_overall_summary(self, all_results: Dict, overall_pass_rate: float):
        """Display overall validation summary"""

        console.print(
            Panel(
                f"[bold]Validation Complete[/bold]\n"
                f"Overall Pass Rate: {overall_pass_rate:.1f}%",
                title="📋 Summary",
                border_style="green"
                if overall_pass_rate >= 75
                else "yellow"
                if overall_pass_rate >= 50
                else "red",
            )
        )

        summary_table = Table(title="Test Summary", box=box.SIMPLE)
        summary_table.add_column("Test", style="cyan")
        summary_table.add_column("Status", justify="center")
        summary_table.add_column("Key Metric", justify="center")

        for test_name, result in all_results.items():
            status = "✅ Pass" if result.get("passed", False) else "❌ Fail"
            status_color = "green" if result.get("passed", False) else "red"

            # Extract key metric based on test type
            if test_name == "obvious_cases":
                key_metric = f"{result.get('success_rate', 0):.1f}% correct"
            elif test_name == "ranking_consistency":
                key_metric = f"{result.get('consistency_rate', 0):.1f}% consistent"
            elif test_name == "score_distribution":
                problems = result.get("problems", [])
                key_metric = f"{len(problems)} issues"
            elif test_name == "edge_cases":
                key_metric = f"{result.get('graceful_handling_rate', 0):.1f}% handled"
            else:
                key_metric = "N/A"

            summary_table.add_row(
                test_name.replace("_", " ").title(),
                f"[{status_color}]{status}[/{status_color}]",
                key_metric,
            )

        console.print(summary_table)

        # Recommendations
        if overall_pass_rate >= 75:
            console.print(
                "\n[green]🎉 Evaluator validation passed! Ready for benchmarking and research.[/green]"
            )
        elif overall_pass_rate >= 50:
            console.print(
                "\n[yellow]⚠️ Evaluator has some issues but may be usable. Review failed tests.[/yellow]"
            )
        else:
            console.print(
                "\n[red]❌ Evaluator has significant issues. Fix core problems before proceeding.[/red]"
            )


def main():
    """Main CLI interface"""

    parser = argparse.ArgumentParser(
        description="Validation Suite for DiffMage Evaluator"
    )
    parser.add_argument("--model", help="AI model to test (default: uses your default)")

    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--all", action="store_true", help="Run all validation tests"
    )
    test_group.add_argument(
        "--test",
        choices=[
            "obvious-cases",
            "ranking-consistency",
            "score-distribution",
            "edge-cases",
        ],
        help="Run specific test",
    )

    parser.add_argument("--output", help="Save results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.test and not args.all:
        args.all = True

    try:
        validator = EvaluationValidator(model_name=args.model)
    except Exception as e:
        console.print(f"[red]Error initializing validator: {e}[/red]")
        console.print(
            "[dim]Make sure you're in the project root and DiffMage is properly installed[/dim]"
        )
        return 1

    results = None

    try:
        if args.all:
            console.print("[blue]Running complete validation suite...[/blue]")
            results = validator.run_all_tests()

        elif args.test == "obvious-cases":
            results = validator.test_obvious_cases()

        elif args.test == "ranking-consistency":
            results = validator.test_ranking_consistency()

        elif args.test == "score-distribution":
            results = validator.test_score_distribution()

        elif args.test == "edge-cases":
            results = validator.test_edge_cases()

        if args.output and results:
            import json

            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"[green]Results saved to {args.output}[/green]")

        if results and results.get("evaluator_ready", results.get("passed", False)):
            console.print("\n[green]✅ Validation completed successfully![/green]")
            return 0
        else:
            console.print("\n[red]❌ Validation found issues that need attention[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Error during validation: {e}[/red]")
        if args.verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return 1


if __name__ == "__main__":
    exit(main())
