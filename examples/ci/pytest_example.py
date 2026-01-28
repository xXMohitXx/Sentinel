"""
Pytest Integration Example

This example shows how to run Phylax checks as part of pytest.
"""

import subprocess
import sys


def test_Phylax_golden_traces():
    """
    Run Phylax check as a pytest test.
    
    This test will:
    1. Replay all blessed (golden) traces
    2. Compare outputs to the golden reference
    3. FAIL if any output differs
    
    Usage:
        pytest examples/ci/pytest_example.py -v
    """
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "check", "--json"],
        capture_output=True,
        text=True,
    )
    
    # Print output for debugging
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Assert exit code is 0 (all golden traces pass)
    assert result.returncode == 0, "Phylax check failed - golden trace regression detected"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
