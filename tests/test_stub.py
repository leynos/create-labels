"""Tests for the generated package stub."""

from __future__ import annotations

import create_labels


def test_hello_returns_stub_greeting() -> None:
    """The generated package exposes a working greeting."""
    assert create_labels.hello() == "hello from Python"
