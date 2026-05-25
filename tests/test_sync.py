"""Unit tests for label synchronisation."""

from __future__ import annotations

import pytest

from create_labels.config import LabelSpec
from create_labels.sync import LabelSyncResult, sync_labels
from tests.test_helpers import make_fake_label, make_fake_repository


def test_sync_labels_creates_missing_labels() -> None:
    """Missing labels are created with the configured metadata."""
    repository = make_fake_repository()

    results = sync_labels(
        repository,
        [LabelSpec("risk: low", "4CAF50", "Low-risk change")],
    )

    assert results == (LabelSyncResult("risk: low", "created"),)
    assert repository.created == [LabelSpec("risk: low", "4CAF50", "Low-risk change")]


def test_sync_labels_updates_existing_labels() -> None:
    """Existing labels are force-updated to match configuration."""
    existing = make_fake_label("risk: low")
    repository = make_fake_repository([existing])

    results = sync_labels(
        repository,
        [LabelSpec("risk: low", "4CAF50", "Low-risk change")],
    )

    assert results == (LabelSyncResult("risk: low", "updated"),)
    assert existing.updates == [LabelSpec("risk: low", "4CAF50", "Low-risk change")]


def test_sync_labels_raises_when_create_returns_no_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed GitHub create response is reported clearly."""
    repository = make_fake_repository()

    def create_label(
        name: str,
        color: str,
        description: str | None = None,
    ) -> None:
        return None

    monkeypatch.setattr(repository, "create_label", create_label)

    with pytest.raises(
        RuntimeError,
        match="GitHub did not return a label after creating 'risk: low'",
    ):
        sync_labels(repository, [LabelSpec("risk: low", "4CAF50", "Low-risk change")])


def test_sync_labels_raises_when_update_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed GitHub update response is reported clearly."""
    existing = make_fake_label("risk: low")
    repository = make_fake_repository([existing])

    def update(name: str, color: str, description: str | None = None) -> bool:
        return False

    monkeypatch.setattr(existing, "update", update)

    with pytest.raises(
        RuntimeError,
        match="GitHub rejected update for label 'risk: low'",
    ):
        sync_labels(repository, [LabelSpec("risk: low", "4CAF50", "Low-risk change")])
