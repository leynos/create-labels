"""Synchronise desired label specs to a GitHub repository-like object.

The module compares configured ``LabelSpec`` instances with repository labels
and creates missing labels or updates existing labels. It deliberately does not
delete labels that are absent from the desired set.

The lightweight ``Protocol`` interfaces model the small github3.py surface used
by this package, which keeps unit and behavioural tests independent from live
GitHub objects.

Example
-------
Synchronise two labels against a github3.py repository object::

    results = sync_labels(github_repository, (LabelSpec("risk: low"),))

Notes
-----
Deletion is not performed; labels outside the iterable are left unchanged.

"""

from __future__ import annotations

import dataclasses
import typing as typ

from github3.exceptions import NotFoundError

if typ.TYPE_CHECKING:
    import collections.abc as cabc

    from .config import LabelSpec


class GitHubLabel(typ.Protocol):
    """Subset of ``github3.issues.label.Label`` used by this package."""

    def update(self, name: str, color: str, description: str | None = None) -> bool:
        """Update this label in place."""


class GitHubRepository(typ.Protocol):
    """Subset of ``github3.repos.repo.Repository`` needed for labels."""

    def label(self, name: str) -> GitHubLabel | None:
        """Return an existing repository label."""

    def create_label(
        self,
        name: str,
        color: str,
        description: str | None = None,
    ) -> GitHubLabel | None:
        """Create a repository label."""


@dataclasses.dataclass(frozen=True, slots=True)
class LabelSyncResult:
    """Outcome of one label synchronisation operation."""

    name: str
    action: typ.Literal["created", "updated"]


def sync_labels(
    repository: GitHubRepository,
    labels: cabc.Iterable[LabelSpec],
) -> tuple[LabelSyncResult, ...]:
    """Create or update labels so the repository matches ``labels``.

    Parameters
    ----------
    repository
        GitHub repository object supporting label lookup, creation, and update.
    labels
        Desired label specifications.

    Returns
    -------
    tuple[LabelSyncResult, ...]
        Per-label results indicating whether each label was created or updated.

    Raises
    ------
    RuntimeError
        Raised when GitHub does not return a created label or rejects an
        update.

    Notes
    -----
    Labels not present in ``labels`` are left unchanged.

    """
    return tuple(_sync_label(repository, label) for label in labels)


def _sync_label(
    repository: GitHubRepository,
    label: LabelSpec,
) -> LabelSyncResult:
    existing_label = _find_label(repository, label.name)
    if existing_label is None:
        created_label = repository.create_label(
            label.name,
            label.color,
            label.description,
        )
        if created_label is None:
            msg = f"GitHub did not return a label after creating {label.name!r}"
            raise RuntimeError(msg)
        return LabelSyncResult(label.name, "created")

    if not existing_label.update(label.name, label.color, label.description):
        msg = f"GitHub rejected update for label {label.name!r}"
        raise RuntimeError(msg)
    return LabelSyncResult(label.name, "updated")


def _find_label(repository: GitHubRepository, name: str) -> GitHubLabel | None:
    try:
        return repository.label(name)
    except NotFoundError:
        return None
