"""Unit tests for label synchronisation."""

from __future__ import annotations

import pytest

from create_labels.config import LabelSpec
from create_labels.sync import LabelSyncResult, sync_labels
from tests.test_helpers import FakeLabel, make_fake_label, make_fake_repository


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


def test_sync_labels_leaves_matching_existing_labels_unchanged() -> None:
    """Existing labels that already match configuration are not updated."""
    existing = make_fake_label("risk: low", "4CAF50", "Low-risk change")
    repository = make_fake_repository([existing])

    results = sync_labels(
        repository,
        [LabelSpec("risk: low", "4CAF50", "Low-risk change")],
    )

    assert results == (LabelSyncResult("risk: low", "unchanged"),)
    assert not existing.updates


def test_sync_labels_normalizes_existing_label_fields_before_comparison() -> None:
    """GitHub field formatting differences do not force redundant updates."""
    existing = make_fake_label("risk: low", "#4caf50", " Low-risk change ")
    repository = make_fake_repository([existing])

    results = sync_labels(
        repository,
        [LabelSpec("risk: low", "4CAF50", "Low-risk change")],
    )

    assert results == (LabelSyncResult("risk: low", "unchanged"),)
    assert not existing.updates


def test_sync_labels_preserves_null_descriptions_when_comparing() -> None:
    """GitHub null descriptions match omitted ``LabelSpec`` descriptions."""
    existing = make_fake_label("needs-review", "#abcdef", None)
    repository = make_fake_repository([existing])

    results = sync_labels(repository, [LabelSpec("needs-review", "ABCDEF")])

    assert results == (LabelSyncResult("needs-review", "unchanged"),)
    assert not existing.updates


def test_sync_labels_url_encodes_names_for_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slash-containing labels are looked up as one encoded path segment."""
    existing = make_fake_label("scope: channel/cli", "1976D2", "CLI channel")
    repository = make_fake_repository([existing])
    lookups: list[str] = []

    def label(name: str) -> FakeLabel | None:
        lookups.append(name)
        if name == "scope%3A%20channel%2Fcli":
            return existing
        return None

    monkeypatch.setattr(repository, "label", label)

    results = sync_labels(
        repository,
        [LabelSpec("scope: channel/cli", "1976D2", "CLI channel")],
    )

    assert lookups == ["scope%3A%20channel%2Fcli"]
    assert results == (LabelSyncResult("scope: channel/cli", "unchanged"),)
    assert not repository.created
    assert not existing.updates


@pytest.mark.parametrize(
    ("patched_callable", "expected_message"),
    [
        (
            "create_label",
            "GitHub did not return a label after creating 'risk: low'",
        ),
        ("update", "GitHub rejected update for label 'risk: low'"),
    ],
)
def test_sync_labels_failure_paths(
    monkeypatch: pytest.MonkeyPatch,
    patched_callable: str,
    expected_message: str,
) -> None:
    """GitHub create and update failures are reported clearly."""
    existing = make_fake_label("risk: low") if patched_callable == "update" else None
    repository = make_fake_repository([existing] if existing is not None else None)

    if patched_callable == "create_label":

        def create_label(
            name: str,
            color: str,
            description: str | None = None,
        ) -> None:
            return None

        monkeypatch.setattr(repository, "create_label", create_label)
    else:
        if existing is None:
            pytest.fail("update failure path requires an existing label")

        def update(name: str, color: str, description: str | None = None) -> bool:
            return False

        monkeypatch.setattr(existing, "update", update)

    with pytest.raises(RuntimeError, match=expected_message):
        sync_labels(repository, [LabelSpec("risk: low", "4CAF50", "Low-risk change")])
