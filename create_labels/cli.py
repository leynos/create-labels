"""Cyclopts command-line interface for create-labels.

This module provides the console entrypoint that wires together argument
parsing, TOML configuration loading, github3.py integration, and result
formatting. ``main`` is the Cyclopts-decorated command used by the
``create-labels`` project script.

Repository resolution prefers ``--repository``, then ``[repository]`` from the
TOML file, then ``GITHUB_REPOSITORY``. Tokens prefer ``--token`` and then
``GITHUB_TOKEN``. API URLs prefer ``--api-url``, then ``github.api_url`` from
TOML, then ``https://api.github.com``.

Examples
--------
Apply the imported default labels::

    create-labels --repository owner/repo

Apply labels from TOML::

    create-labels --config labels.toml

Target GitHub Enterprise or a simulator::

    create-labels --repository owner/repo --api-url https://github.example/api/v3

"""

from __future__ import annotations

import pathlib

from cyclopts import App

from .config import LabelConfig, RepositorySpec, load_config
from .github import sync_repository_labels

app: App = App(help="Create or update GitHub repository labels from TOML.")


@app.default
def main(
    *,
    config: str | None = None,
    repository: str | None = None,
    token: str | None = None,
    api_url: str | None = None,
) -> None:
    """Create or update labels in a GitHub repository.

    Parameters
    ----------
    config
        TOML configuration path. When omitted, the default imported labels are
        used.
    repository
        Repository in ``owner/name`` form. Overrides ``[repository]`` in the
        TOML file and ``GITHUB_REPOSITORY``.
    token
        GitHub token. When omitted, ``GITHUB_TOKEN`` is used.
    api_url
        GitHub API URL. Use this for GitHub Enterprise or local simulators.

    """
    label_config = (
        load_config(pathlib.Path(config))
        if config is not None
        else LabelConfig(None, ())
    )
    results = sync_repository_labels(
        config=label_config,
        repository=_parse_repository_argument(repository),
        token=token,
        api_url=api_url,
    )

    for result in results:
        print(f"{result.action}: {result.name}")


def _parse_repository_argument(repository: str | None) -> RepositorySpec | None:
    """Parse an ``owner/name`` repository argument into a RepositorySpec."""
    if repository is None:
        return None

    owner, separator, name = repository.partition("/")
    if not all((separator, owner, name)) or "/" in name:
        msg = "repository must use the owner/name format"
        raise ValueError(msg)
    return RepositorySpec(owner=owner, name=name)


def run() -> None:
    """Execute the Cyclopts application.

    This thin wrapper delegates to ``app`` so packaging can expose a stable
    project-script entrypoint.

    Raises
    ------
    SystemExit
        Raised by Cyclopts when argument parsing or command execution fails.

    """
    app()
