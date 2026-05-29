"""Behavioural tests for label synchronisation."""

from __future__ import annotations

import typing as typ

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from create_labels.config import LabelSpec
from create_labels.sync import LabelSyncResult, sync_labels
from tests.test_helpers import FakeRepository, make_fake_label, make_fake_repository

scenarios("../features/synchronise_labels.feature")

_LOW_RISK_COLOR = "4CAF50"
_LOW_RISK_DESC = "Low risk"
_HIGH_RISK_COLOR = "F44336"
_HIGH_RISK_DESC = "High risk"


class LabelSyncContext(typ.TypedDict):
    """Shared state for a label synchronisation scenario."""

    repository: FakeRepository
    labels: tuple[LabelSpec, ...]
    results: tuple[LabelSyncResult, ...]


@pytest.fixture
def label_sync_context() -> LabelSyncContext:
    """Provide scenario state."""
    return {
        "repository": make_fake_repository(),
        "labels": (),
        "results": (),
    }


@given(parsers.parse('a repository with an existing "{name}" label'))
def given_existing_label(label_sync_context: LabelSyncContext, name: str) -> None:
    """Create a repository label before synchronisation."""
    label_sync_context["repository"].labels[name] = make_fake_label(name)


@given(parsers.parse('a label configuration containing "{low}" and "{high}"'))
def given_label_configuration(
    label_sync_context: LabelSyncContext,
    low: str,
    high: str,
) -> None:
    """Create the desired label configuration."""
    label_sync_context["labels"] = (
        LabelSpec(low, _LOW_RISK_COLOR, _LOW_RISK_DESC),
        LabelSpec(high, _HIGH_RISK_COLOR, _HIGH_RISK_DESC),
    )


@when("the labels are synchronised")
def when_labels_are_synchronised(label_sync_context: LabelSyncContext) -> None:
    """Synchronise configured labels."""
    label_sync_context["results"] = sync_labels(
        label_sync_context["repository"],
        label_sync_context["labels"],
    )


@then(parsers.parse('the existing "{name}" label is updated'))
def then_existing_label_is_updated(
    label_sync_context: LabelSyncContext,
    name: str,
) -> None:
    """Check the existing label was updated."""
    label = label_sync_context["repository"].labels[name]
    assert label.updates == [LabelSpec(name, _LOW_RISK_COLOR, _LOW_RISK_DESC)], (
        f"expected updates to contain low-risk LabelSpec for {name}"
    )
    assert LabelSyncResult(name, "updated") in label_sync_context["results"], (
        f"expected label sync results to include updated result for {name}"
    )


@then(parsers.parse('the missing "{name}" label is created'))
def then_missing_label_is_created(
    label_sync_context: LabelSyncContext,
    name: str,
) -> None:
    """Check the missing label was created."""
    assert (
        LabelSpec(name, _HIGH_RISK_COLOR, _HIGH_RISK_DESC)
        in label_sync_context["repository"].created
    ), f"expected created labels to contain {name} with correct color/desc"
    assert LabelSyncResult(name, "created") in label_sync_context["results"], (
        f"expected label sync results to include created result for {name}"
    )
