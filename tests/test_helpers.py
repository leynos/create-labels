"""Shared test doubles for label synchronisation tests."""

from __future__ import annotations

import urllib.parse

from create_labels.config import LabelSpec


class FakeLabel:
    """In-memory label object with the github3.py update shape."""

    def __init__(self, name: str, color: str, description: str | None) -> None:
        self.name = name
        self.color = color
        self.description = description
        self.updates: list[LabelSpec] = []

    def update(self, name: str, color: str, description: str | None = None) -> bool:
        """Record an update and return success."""
        self.name = name
        self.color = color
        self.description = description
        self.updates.append(LabelSpec(name, color, description))
        return True


class FakeRepository:
    """In-memory repository with the subset of github3.py used by sync."""

    def __init__(self, labels: list[FakeLabel] | None = None) -> None:
        self.labels = {label.name: label for label in labels or []}
        self.created: list[LabelSpec] = []

    def label(self, name: str) -> FakeLabel | None:
        """Return an existing label or None."""
        return self.labels.get(urllib.parse.unquote(name))

    def create_label(
        self,
        name: str,
        color: str,
        description: str | None = None,
    ) -> FakeLabel | None:
        """Create and record a new label."""
        label = FakeLabel(name, color, description)
        self.labels[name] = label
        self.created.append(LabelSpec(name, color, description))
        return label


def make_fake_label(
    name: str,
    color: str = "FFFFFF",
    description: str | None = None,
) -> FakeLabel:
    """Build a fake label."""
    return FakeLabel(name, color, description)


def make_fake_repository(labels: list[FakeLabel] | None = None) -> FakeRepository:
    """Build a fake repository."""
    return FakeRepository(labels)
