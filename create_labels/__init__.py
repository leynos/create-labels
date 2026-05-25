"""Create and update GitHub repository labels."""

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
