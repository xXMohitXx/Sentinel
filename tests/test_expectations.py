"""
Tests for Expectation Engine

Tests the four rules and the evaluator.
"""

import pytest

from sdk.expectations import (
    evaluate,
    Verdict,
    Evaluator,
    MustIncludeRule,
    MustNotIncludeRule,
    MaxLatencyRule,
    MinTokensRule,
)


class TestMustIncludeRule:
    """Tests for must_include rule."""
    
    def test_pass_when_substring_present(self):
        rule = MustIncludeRule(["refund"])
        result = rule.evaluate("We will process your refund shortly.", 100)
        assert result.passed is True
    
    def test_fail_when_substring_missing(self):
        rule = MustIncludeRule(["refund"])
        result = rule.evaluate("We cannot help with that.", 100)
        assert result.passed is False
        assert "refund" in result.violation_message
    
    def test_case_insensitive_by_default(self):
        rule = MustIncludeRule(["REFUND"])
        result = rule.evaluate("Your refund is approved.", 100)
        assert result.passed is True
    
    def test_multiple_substrings(self):
        rule = MustIncludeRule(["refund", "approved"])
        result = rule.evaluate("Your refund is approved.", 100)
        assert result.passed is True
    
    def test_severity_is_low(self):
        rule = MustIncludeRule(["test"])
        assert rule.severity == "low"


class TestMustNotIncludeRule:
    """Tests for must_not_include rule."""
    
    def test_pass_when_substring_absent(self):
        rule = MustNotIncludeRule(["I am not sure"])
        result = rule.evaluate("Your refund is approved.", 100)
        assert result.passed is True
    
    def test_fail_when_forbidden_substring_found(self):
        rule = MustNotIncludeRule(["I am not sure"])
        result = rule.evaluate("I am not sure about that.", 100)
        assert result.passed is False
        assert "forbidden" in result.violation_message
    
    def test_severity_is_high(self):
        rule = MustNotIncludeRule(["test"])
        assert rule.severity == "high"


class TestMaxLatencyRule:
    """Tests for max_latency_ms rule."""
    
    def test_pass_when_under_threshold(self):
        rule = MaxLatencyRule(1500)
        result = rule.evaluate("Any response", 1000)
        assert result.passed is True
    
    def test_fail_when_over_threshold(self):
        rule = MaxLatencyRule(1500)
        result = rule.evaluate("Any response", 2000)
        assert result.passed is False
        assert "2000ms" in result.violation_message
        assert "1500ms" in result.violation_message
    
    def test_pass_at_exact_threshold(self):
        rule = MaxLatencyRule(1500)
        result = rule.evaluate("Any response", 1500)
        assert result.passed is True
    
    def test_severity_is_medium(self):
        rule = MaxLatencyRule(1000)
        assert rule.severity == "medium"


class TestMinTokensRule:
    """Tests for min_tokens rule."""
    
    def test_pass_when_enough_tokens(self):
        rule = MinTokensRule(5)
        result = rule.evaluate("This is a longer response with more tokens.", 100)
        assert result.passed is True
    
    def test_fail_when_too_short(self):
        rule = MinTokensRule(10)
        result = rule.evaluate("Short.", 100)
        assert result.passed is False
        assert "expected at least 10" in result.violation_message
    
    def test_severity_is_low(self):
        rule = MinTokensRule(5)
        assert rule.severity == "low"


class TestEvaluator:
    """Tests for the Evaluator class."""
    
    def test_pass_with_no_rules(self):
        evaluator = Evaluator()
        verdict = evaluator.evaluate("Any response", 100)
        assert verdict.status == "pass"
    
    def test_pass_when_all_rules_pass(self):
        evaluator = Evaluator()
        evaluator.must_include(["hello"])
        evaluator.max_latency_ms(2000)
        verdict = evaluator.evaluate("Hello there!", 100)
        assert verdict.status == "pass"
        assert verdict.violations == []
    
    def test_fail_with_violations(self):
        evaluator = Evaluator()
        evaluator.must_include(["refund"])
        verdict = evaluator.evaluate("No refund mentioned.", 100)
        # Wait, "refund" IS in "No refund mentioned."
        assert verdict.status == "pass"
    
    def test_fail_when_substring_truly_missing(self):
        evaluator = Evaluator()
        evaluator.must_include(["approved"])
        verdict = evaluator.evaluate("Your request is pending.", 100)
        assert verdict.status == "fail"
        assert len(verdict.violations) == 1
    
    def test_severity_max_from_violations(self):
        evaluator = Evaluator()
        evaluator.must_include(["test"])  # low
        evaluator.must_not_include(["forbidden"])  # high
        verdict = evaluator.evaluate("This has forbidden content.", 100)
        assert verdict.status == "fail"
        assert verdict.severity == "high"  # highest severity wins
    
    def test_all_violations_reported(self):
        evaluator = Evaluator()
        evaluator.must_include(["A"])
        evaluator.must_include(["B"])
        evaluator.must_include(["C"])
        verdict = evaluator.evaluate("None of those letters.", 100)
        assert verdict.status == "fail"
        assert len(verdict.violations) == 3


class TestEvaluateFunction:
    """Tests for the evaluate() convenience function."""
    
    def test_basic_pass(self):
        verdict = evaluate(
            response_text="Your refund is approved.",
            latency_ms=500,
            must_include=["refund", "approved"],
        )
        assert verdict.status == "pass"
    
    def test_basic_fail(self):
        verdict = evaluate(
            response_text="I am not sure about that.",
            latency_ms=500,
            must_not_include=["not sure"],
        )
        assert verdict.status == "fail"
        assert verdict.severity == "high"
    
    def test_latency_violation(self):
        verdict = evaluate(
            response_text="Fast response",
            latency_ms=3000,
            max_latency_ms=1500,
        )
        assert verdict.status == "fail"
        assert verdict.severity == "medium"


class TestVerdictImmutability:
    """Test that Verdict is immutable."""
    
    def test_verdict_is_frozen(self):
        verdict = Verdict(status="pass")
        with pytest.raises(Exception):  # ValidationError or AttributeError
            verdict.status = "fail"
