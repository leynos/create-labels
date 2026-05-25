"""Unit tests for label configuration parsing."""

from __future__ import annotations

import typing as typ

import pytest

from create_labels.config import ConfigError, LabelSpec, load_config, parse_config
from create_labels.defaults import DEFAULT_LABELS

if typ.TYPE_CHECKING:
    import pathlib


def test_default_labels_import_original_shell_script_set() -> None:
    """The default package data preserves the imported bootstrap labels."""
    # DEFAULT_LABELS mirrors the shell script groups:
    # size:5 + risk:4 + scope:30 + ecosystem:3 + workflow:1 + contributor:4 = 47.
    assert len(DEFAULT_LABELS) == 47
    assert DEFAULT_LABELS[0] == LabelSpec(
        "size: XS",
        "F9D0C4",
        "< 10 changed lines (excluding docs)",
    )
    assert DEFAULT_LABELS[-1] == LabelSpec(
        "contributor: core",
        "FF8A65",
        "20+ merged PRs",
    )
    assert (
        LabelSpec(
            "dependencies",
            "0366D6",
            "Dependency updates and dependency manager pull requests",
        )
        in DEFAULT_LABELS
    )
    assert (
        LabelSpec("github-actions", "2088FF", "GitHub Actions workflow updates")
        in DEFAULT_LABELS
    )
    assert LabelSpec("cargo", "DEA584", "Rust Cargo package and lockfile updates") in (
        DEFAULT_LABELS
    )


def test_load_config_parses_repository_api_url_and_optional_label_fields(
    tmp_path: pathlib.Path,
) -> None:
    """TOML config can override repository, API URL, colour, and description."""
    config_path = tmp_path / "labels.toml"
    config_path.write_text(
        """
        [repository]
        owner = "leynos"
        name = "create-labels"

        [github]
        api_url = "http://127.0.0.1:1234/"

        [[labels]]
        name = "needs-review"
        color = "#abcdef"
        description = "Ready for review"

        [[labels]]
        name = "plain-label"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.repository is not None
    assert config.repository.full_name == "leynos/create-labels"
    # config.api_url intentionally drops a trailing slash for stable base URLs.
    assert config.api_url == "http://127.0.0.1:1234"
    assert config.labels == (
        LabelSpec("needs-review", "ABCDEF", "Ready for review"),
        LabelSpec("plain-label"),
    )


def test_config_rejects_slash_only_api_url(tmp_path: pathlib.Path) -> None:
    """Slash-only API URLs are empty after normalization and must fail."""
    with pytest.raises(ConfigError, match=r"github\.api_url"):
        parse_config({"github": {"api_url": "/"}})

    config_path = tmp_path / "labels.toml"
    config_path.write_text(
        """
        [github]
        api_url = " / "
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match=r"github\.api_url"):
        load_config(config_path)


def test_parse_config_rejects_duplicate_labels() -> None:
    """Duplicate label names would make sync order ambiguous."""
    with pytest.raises(ConfigError, match="Duplicate label definitions"):
        parse_config({
            "labels": [
                {"name": "risk: low"},
                {"name": "Risk: Low"},
            ],
        })


def test_parse_config_rejects_malformed_colours() -> None:
    """GitHub label colours must be six hex digits."""
    with pytest.raises(ConfigError, match="invalid colour"):
        parse_config({"labels": [{"name": "broken", "color": "blue"}]})
