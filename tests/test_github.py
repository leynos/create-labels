"""Unit tests for GitHub adapter error handling."""

from __future__ import annotations

import pytest

from create_labels.config import LabelConfig, RepositorySpec
from create_labels.github import GitHubError, sync_repository_labels


def test_sync_repository_labels_requires_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repository coordinates must come from CLI, config, or environment."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    auth_value = "sample-auth-value"

    with pytest.raises(GitHubError, match="Repository must be provided"):
        sync_repository_labels(
            config=LabelConfig(None, ()),
            repository=None,
            token=auth_value,
            api_url=None,
        )


def test_sync_repository_labels_rejects_malformed_environment_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed ``GITHUB_REPOSITORY`` values are reported clearly."""
    auth_value = "sample-auth-value"
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/name/extra")

    with pytest.raises(GitHubError, match="owner/name format"):
        sync_repository_labels(
            config=LabelConfig(None, ()),
            repository=None,
            token=auth_value,
            api_url=None,
        )


def test_sync_repository_labels_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Authentication must come from CLI or ``GITHUB_TOKEN``."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with pytest.raises(GitHubError, match="GitHub token"):
        sync_repository_labels(
            config=LabelConfig(None, ()),
            repository=RepositorySpec("owner", "repo"),
            token=None,
            api_url=None,
        )
