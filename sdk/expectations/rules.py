"""
Expectation Rules

Four deterministic rules for LLM response validation:
- must_include: Substring(s) must appear
- must_not_include: Substring(s) must NOT appear  
- max_latency_ms: Latency ceiling
- min_tokens: Minimum response length

Each rule has an associated severity:
- high: Critical failures (must_not_include violations)
- medium: Performance issues (latency violations)
- low: Quality issues (length/content expectations)
"""

from abc import ABC, abstractmethod
from typing import Literal

SeverityLevel = Literal["low", "medium", "high"]


class RuleResult:
    """Result of evaluating a single rule."""
    
    def __init__(
        self,
        passed: bool,
        rule_name: str,
        severity: SeverityLevel,
        violation_message: str = "",
    ):
        self.passed = passed
        self.rule_name = rule_name
        self.severity = severity
        self.violation_message = violation_message
    
    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"RuleResult({self.rule_name}: {status})"


class Rule(ABC):
    """Base class for expectation rules."""
    
    name: str = "base_rule"
    severity: SeverityLevel = "medium"
    
    @abstractmethod
    def evaluate(self, response_text: str, latency_ms: int) -> RuleResult:
        """
        Evaluate the rule against a response.
        
        Args:
            response_text: The LLM response text
            latency_ms: Response latency in milliseconds
            
        Returns:
            RuleResult indicating pass/fail and violation details
        """
        pass


class MustIncludeRule(Rule):
    """
    Response must include specified substring(s).
    
    Severity: low (missing content is quality issue, not critical)
    """
    
    name = "must_include"
    severity: SeverityLevel = "low"
    
    def __init__(self, substrings: list[str], case_sensitive: bool = False):
        """
        Args:
            substrings: List of substrings that must appear
            case_sensitive: Whether to match case-sensitively
        """
        self.substrings = substrings
        self.case_sensitive = case_sensitive
    
    def evaluate(self, response_text: str, latency_ms: int) -> RuleResult:
        text = response_text if self.case_sensitive else response_text.lower()
        
        missing = []
        for substring in self.substrings:
            check = substring if self.case_sensitive else substring.lower()
            if check not in text:
                missing.append(substring)
        
        if missing:
            return RuleResult(
                passed=False,
                rule_name=self.name,
                severity=self.severity,
                violation_message=f"missing substring(s): {missing}",
            )
        
        return RuleResult(
            passed=True,
            rule_name=self.name,
            severity=self.severity,
        )


class MustNotIncludeRule(Rule):
    """
    Response must NOT include specified substring(s).
    
    Severity: high (forbidden content is critical failure)
    """
    
    name = "must_not_include"
    severity: SeverityLevel = "high"
    
    def __init__(self, substrings: list[str], case_sensitive: bool = False):
        """
        Args:
            substrings: List of substrings that must NOT appear
            case_sensitive: Whether to match case-sensitively
        """
        self.substrings = substrings
        self.case_sensitive = case_sensitive
    
    def evaluate(self, response_text: str, latency_ms: int) -> RuleResult:
        text = response_text if self.case_sensitive else response_text.lower()
        
        found = []
        for substring in self.substrings:
            check = substring if self.case_sensitive else substring.lower()
            if check in text:
                found.append(substring)
        
        if found:
            return RuleResult(
                passed=False,
                rule_name=self.name,
                severity=self.severity,
                violation_message=f"forbidden substring(s) found: {found}",
            )
        
        return RuleResult(
            passed=True,
            rule_name=self.name,
            severity=self.severity,
        )


class MaxLatencyRule(Rule):
    """
    Response latency must not exceed threshold.
    
    Severity: medium (performance issue)
    """
    
    name = "max_latency_ms"
    severity: SeverityLevel = "medium"
    
    def __init__(self, max_ms: int):
        """
        Args:
            max_ms: Maximum allowed latency in milliseconds
        """
        self.max_ms = max_ms
    
    def evaluate(self, response_text: str, latency_ms: int) -> RuleResult:
        if latency_ms > self.max_ms:
            return RuleResult(
                passed=False,
                rule_name=self.name,
                severity=self.severity,
                violation_message=f"latency {latency_ms}ms exceeds max {self.max_ms}ms",
            )
        
        return RuleResult(
            passed=True,
            rule_name=self.name,
            severity=self.severity,
        )


class MinTokensRule(Rule):
    """
    Response must have at least N tokens (approximated by word count).
    
    Severity: low (length expectation is quality issue)
    """
    
    name = "min_tokens"
    severity: SeverityLevel = "low"
    
    def __init__(self, min_tokens: int):
        """
        Args:
            min_tokens: Minimum number of tokens (approximated by words)
        """
        self.min_tokens = min_tokens
    
    def evaluate(self, response_text: str, latency_ms: int) -> RuleResult:
        # Approximate token count by word count
        # More accurate would be to use actual tokenizer, but that adds dependency
        word_count = len(response_text.split())
        
        if word_count < self.min_tokens:
            return RuleResult(
                passed=False,
                rule_name=self.name,
                severity=self.severity,
                violation_message=f"response has ~{word_count} tokens, expected at least {self.min_tokens}",
            )
        
        return RuleResult(
            passed=True,
            rule_name=self.name,
            severity=self.severity,
        )
