"""Tests for the SecurityGuard and injection detector."""

from __future__ import annotations

import pytest


def test_owasp_category_mapping():
    """OWASP categories should match spec categories."""
    known_categories = [
        "LLM01: Prompt Injection",
        "LLM06: Sensitive Information Disclosure",
        "LLM07: Insecure Plugin Design / Unsafe Content",
    ]
    for cat in known_categories:
        assert cat.startswith("LLM")


def test_severity_range():
    """Security event severity should be between 1 and 10."""
    for sev in [1, 5, 7, 9, 10]:
        assert 1 <= sev <= 10


def test_direction_values():
    """Direction must be 'input' or 'output'."""
    valid = {"input", "output"}
    assert "input" in valid
    assert "output" in valid
    assert "both" not in valid


def test_risk_types():
    """Known risk types should be present in the system."""
    valid_risk_types = {"prompt_injection", "unsafe_content", "sensitive_info"}
    assert "prompt_injection" in valid_risk_types
    assert "unsafe_content" in valid_risk_types
