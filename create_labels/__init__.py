"""Public API for create-labels.

The package root is the stable import boundary for library consumers. It
re-exports typed configuration values from ``create_labels.config``, the
imported default label set from ``create_labels.defaults``, and the pure label
synchronisation function and result type from ``create_labels.sync``.

Use these exports when embedding create-labels in tests, scripts, or other
tools. The submodules keep parsing, default data, GitHub integration, and sync
decisions separate, while this module provides the small public surface that
callers should depend on.
"""

from __future__ import annotations

from .config import LabelConfig, LabelSpec, RepositorySpec, load_config
from .defaults import DEFAULT_LABELS
from .sync import LabelSyncResult, sync_labels

__all__ = [
    "DEFAULT_LABELS",
    "LabelConfig",
    "LabelSpec",
    "LabelSyncResult",
    "RepositorySpec",
    "load_config",
    "sync_labels",
]
