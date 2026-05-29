"""github3.py adapter for repository label synchronisation.

This module connects the pure label synchronisation logic to GitHub through
github3.py. ``sync_repository_labels`` resolves repository coordinates,
authentication, and API URL fallbacks before fetching the repository object and
delegating label creation or update work to ``sync_labels``.

Resolution order is explicit argument first, then TOML configuration, then the
environment where applicable: repository uses ``RepositorySpec`` or
``LabelConfig.repository`` or ``GITHUB_REPOSITORY``; token uses ``--token`` or
``GITHUB_TOKEN``; API URL uses the explicit argument or ``LabelConfig.api_url``
or ``https://api.github.com``.

Example
-------
Synchronise labels for one repository::

    config = LabelConfig(RepositorySpec("owner", "repo"), labels)
    sync_repository_labels(
        config=config,
        repository=None,
        token="ghp_example",
        api_url=None,
    )

"""

from __future__ import annotations

import os
import typing as typ
import urllib.parse

import github3
from github3.exceptions import NotFoundError
from github3.session import GitHubSession

from .config import LabelConfig, RepositorySpec
from .defaults import DEFAULT_LABELS
from .sync import GitHubLabel, LabelSyncResult, sync_labels

if typ.TYPE_CHECKING:
    import collections.abc as cabc

    from .config import LabelSpec

DEFAULT_API_URL = "https://api.github.com"


class GitHubError(RuntimeError):
    """Raised when GitHub configuration or API access fails."""


class _Github3Repository(typ.Protocol):
    """github3.py repository methods used by the adapter."""

    def label(self, name: str) -> GitHubLabel | None:
        """Return a label by name."""

    def create_label(
        self,
        name: str,
        color: str,
        description: str | None = None,
    ) -> GitHubLabel | None:
        """Create a label."""


def sync_repository_labels(
    *,
    config: LabelConfig,
    repository: RepositorySpec | None,
    token: str | None,
    api_url: str | None,
) -> tuple[LabelSyncResult, ...]:
    """Synchronise configured labels to a GitHub repository.

    Parameters
    ----------
    config
        Parsed label configuration, including optional repository, labels, and
        API URL.
    repository
        Explicit repository override. When omitted, ``config.repository`` and
        then ``GITHUB_REPOSITORY`` are used.
    token
        Explicit API token. When omitted, ``GITHUB_TOKEN`` is used.
    api_url
        Explicit GitHub API URL. When omitted, ``config.api_url`` and then the
        public GitHub API are used.

    Returns
    -------
    tuple[LabelSyncResult, ...]
        Per-label create or update results.

    Raises
    ------
    GitHubError
        Raised when repository coordinates, authentication, or repository
        lookup fail.
    RuntimeError
        Raised when GitHub rejects a label create or update operation.

    Notes
    -----
    This function resolves the repository, authenticates with ``_login``,
    fetches the github3.py repository object, chooses configured labels or
    ``DEFAULT_LABELS`` via ``_effective_labels``, and delegates to
    ``sync_labels``.

    """
    resolved_repository = repository or config.repository or _repository_from_env()
    if resolved_repository is None:
        msg = "Repository must be provided via CLI, config, or GITHUB_REPOSITORY"
        raise GitHubError(msg)

    github = _login(token=token, api_url=api_url or config.api_url)
    github_repository = github.repository(
        resolved_repository.owner,
        resolved_repository.name,
    )
    if github_repository is None:
        msg = f"GitHub repository not found: {resolved_repository.full_name}"
        raise GitHubError(msg)

    labels = _effective_labels(config.labels)
    return sync_labels(_GitHubRepositoryAdapter(github_repository), labels)


class _GitHubRepositoryAdapter:
    """Translate github3.py repository behaviour into the sync protocol."""

    def __init__(self, repository: _Github3Repository) -> None:
        """Store the github3.py repository object to adapt."""
        self._repository = repository

    def label(self, name: str) -> GitHubLabel | None:
        """Return a label or None when github3.py reports it missing."""
        try:
            encoded_name = urllib.parse.quote(name, safe="")
            return self._repository.label(encoded_name)
        except NotFoundError:
            return None

    def create_label(
        self,
        name: str,
        color: str,
        description: str | None = None,
    ) -> GitHubLabel | None:
        """Create a repository label through github3.py."""
        return self._repository.create_label(name, color, description)


def _login(token: str | None, api_url: str | None) -> github3.GitHub:
    """Resolve token and API URL, then return a GitHub client."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    if not resolved_token:
        msg = "GitHub token must be provided via --token or GITHUB_TOKEN"
        raise GitHubError(msg)

    resolved_api_url = (api_url or DEFAULT_API_URL).rstrip("/")
    if resolved_api_url == DEFAULT_API_URL:
        return github3.login(token=resolved_token)

    session = GitHubSession()
    session.base_url = resolved_api_url
    return github3.GitHub(token=resolved_token, session=session)


def _repository_from_env() -> RepositorySpec | None:
    """Parse ``GITHUB_REPOSITORY`` into ``RepositorySpec`` or return None."""
    raw_repository = os.environ.get("GITHUB_REPOSITORY")
    if raw_repository is None:
        return None

    owner, separator, name = raw_repository.partition("/")
    if not all((separator, owner, name)) or "/" in name:
        msg = "GITHUB_REPOSITORY must use the owner/name format"
        raise GitHubError(msg)
    return RepositorySpec(owner=owner, name=name)


def _effective_labels(labels: cabc.Sequence[LabelSpec]) -> tuple[LabelSpec, ...]:
    """Return provided labels as a tuple, or ``DEFAULT_LABELS``."""
    if labels:
        return tuple(labels)
    return DEFAULT_LABELS
