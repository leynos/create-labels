"""Unit tests for the Cyclopts command implementation."""

from __future__ import annotations

import typing as typ

import pytest

from create_labels import cli
from create_labels.config import LabelConfig, RepositorySpec
from create_labels.sync import LabelSyncResult

_SYNC_CALL_KEYS = frozenset({"config", "repository", "token", "api_url"})
_MALFORMED_REPOSITORIES = ("", "owner", "owner/", "/name", "owner/name/extra")

if typ.TYPE_CHECKING:
    import pathlib


class SyncCall:
    """Test double for ``sync_repository_labels`` used by CLI tests.

    ``SyncCall`` records the keyword arguments passed by ``cli.main`` and
    returns a deterministic ``LabelSyncResult`` for assertions. It raises
    ``AssertionError`` on unexpected keyword names so CLI wiring changes fail
    close to the call site.
    """

    def __init__(self) -> None:
        self.config: LabelConfig | None = None
        self.repository: RepositorySpec | None = None
        self.token: str | None = None
        self.api_url: str | None = None

    def __call__(self, **kwargs: object) -> tuple[LabelSyncResult, ...]:
        """Record the sync invocation."""
        unexpected_keys = set(kwargs) - _SYNC_CALL_KEYS
        if unexpected_keys:
            msg = f"Unexpected sync kwargs: {sorted(unexpected_keys)}"
            raise AssertionError(msg)

        self.config = typ.cast("LabelConfig", kwargs["config"])
        self.repository = typ.cast("RepositorySpec | None", kwargs["repository"])
        self.token = typ.cast("str | None", kwargs["token"])
        self.api_url = typ.cast("str | None", kwargs["api_url"])
        return (LabelSyncResult("risk: low", "created"),)


def test_main_loads_config_and_prints_sync_results(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI command wires config and repository overrides into sync."""
    config_path = tmp_path / "labels.toml"
    config_path.write_text(
        """
        [[labels]]
        name = "risk: low"
        color = "4CAF50"
        """,
        encoding="utf-8",
    )
    sync_call = SyncCall()
    auth_value = "sample-auth-value"
    monkeypatch.setattr(cli, "sync_repository_labels", sync_call)

    cli.main(
        config=str(config_path),
        repository="owner/repo",
        token=auth_value,
        api_url="http://localhost:3000",
    )

    assert sync_call.config is not None, "expected sync_call.config to be set"
    assert len(sync_call.config.labels) == 1, "expected exactly one configured label"
    assert sync_call.config.labels[0].name == "risk: low", (
        "expected first label name to be risk: low"
    )
    assert sync_call.repository == RepositorySpec(
        "owner",
        "repo",
    ), "expected parsed repository override"
    assert sync_call.token == auth_value, "expected token to match auth_value"
    assert sync_call.api_url == "http://localhost:3000", (
        "expected api_url to be http://localhost:3000"
    )
    assert capsys.readouterr().out == "created: risk: low\n", (
        "expected stdout to contain created result"
    )


@pytest.mark.parametrize("repository", _MALFORMED_REPOSITORIES)
def test_main_rejects_malformed_repository(repository: str) -> None:
    """Repository CLI values must use owner/name form."""
    with pytest.raises(ValueError, match="owner/name"):
        cli.main(repository=repository)
