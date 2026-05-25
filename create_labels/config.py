"""TOML configuration loading for GitHub label synchronisation.

This module owns the typed configuration boundary for the package. It loads
TOML data into ``RepositorySpec``, ``LabelSpec``, and ``LabelConfig`` values,
normalises six-digit hex colours, validates label names, and rejects duplicate
label definitions before any GitHub API calls are made.

Example usage
-------------
Load a TOML file from disk::

    config = load_config(Path("labels.toml"))

Parse data that has already been decoded from TOML::

    config = parse_config({"labels": [{"name": "risk: low"}]})

"""

from __future__ import annotations

import collections.abc as cabc
import dataclasses
import re
import tomllib
import typing as typ

if typ.TYPE_CHECKING:
    import pathlib

DEFAULT_COLOR = "EDEDED"
_HEX_COLOR = re.compile(r"\A[0-9A-F]{6}\Z")


class ConfigError(ValueError):
    """Raised when a label configuration file is invalid.

    Parameters
    ----------
    *args : object
        Error message values passed to ``ValueError``.

    """


@dataclasses.dataclass(frozen=True, slots=True)
class RepositorySpec:
    """GitHub repository coordinates.

    Attributes
    ----------
    owner : str
        GitHub account or organisation that owns the repository.
    name : str
        Repository name within ``owner``.
    full_name : str
        Property returning the canonical ``owner/name`` repository name.

    """

    owner: str
    name: str

    @property
    def full_name(self) -> str:
        """Return the canonical ``owner/name`` repository name."""
        return f"{self.owner}/{self.name}"


@dataclasses.dataclass(frozen=True, slots=True)
class LabelSpec:
    """Desired state for a GitHub repository label.

    Attributes
    ----------
    name : str
        Label name shown in GitHub.
    color : str
        Six-character hexadecimal label colour without a leading ``#``.
    description : str | None
        Optional label description shown in GitHub.

    Raises
    ------
    ConfigError
        Raised by ``__post_init__`` when ``name`` is empty or ``color`` is not
        a valid six-character hexadecimal colour.

    Notes
    -----
    ``__post_init__`` normalises ``name``, ``color``, and ``description`` by
    trimming surrounding whitespace and converting colours to uppercase
    six-character hexadecimal values.

    """

    name: str
    color: str = DEFAULT_COLOR
    description: str | None = None

    def __post_init__(self) -> None:
        """Normalise and validate colour format; reject malformed labels."""
        name = self.name.strip()
        if not name:
            msg = "Label names must not be empty"
            raise ConfigError(msg)

        color = self.color.removeprefix("#").upper()
        description = self.description.strip() if self.description is not None else None
        if _HEX_COLOR.fullmatch(color) is None:
            msg = f"Label {name!r} has invalid colour {self.color!r}"
            raise ConfigError(msg)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "color", color)
        object.__setattr__(self, "description", description)


@dataclasses.dataclass(frozen=True, slots=True)
class LabelConfig:
    """Complete label synchronisation configuration.

    Attributes
    ----------
    repository : RepositorySpec | None
        Optional repository coordinates from configuration.
    labels : tuple[LabelSpec, ...]
        Desired labels to create or update.
    api_url : str | None
        Optional GitHub API base URL.

    """

    repository: RepositorySpec | None
    labels: tuple[LabelSpec, ...]
    api_url: str | None = None


def load_config(path: pathlib.Path) -> LabelConfig:
    """Load and validate a TOML label configuration file.

    Parameters
    ----------
    path
        Path to the TOML configuration file.

    Returns
    -------
    LabelConfig
        Parsed repository, label, and optional GitHub API URL configuration.

    Raises
    ------
    ConfigError
        Raised when the file cannot be read, TOML decoding fails, or the
        decoded configuration is invalid.

    """
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        msg = f"Invalid TOML in {path}: {exc}"
        raise ConfigError(msg) from exc
    except OSError as exc:
        msg = f"Could not read label configuration {path}: {exc}"
        raise ConfigError(msg) from exc

    return parse_config(parsed)


def parse_config(config: cabc.Mapping[str, typ.Any]) -> LabelConfig:
    """Parse raw TOML data into a typed label configuration.

    Parameters
    ----------
    config
        Mapping decoded from TOML.

    Returns
    -------
    LabelConfig
        Parsed configuration containing repository coordinates, label specs,
        and an optional GitHub API URL.

    Raises
    ------
    ConfigError
        Raised when repository, label, or GitHub API URL fields fail
        validation.

    Notes
    -----
    The parser delegates to ``_parse_repository``, ``_parse_labels``, and
    ``_parse_api_url`` so each section has one validation boundary.

    """
    return LabelConfig(
        repository=_parse_repository(config.get("repository")),
        labels=_parse_labels(config.get("labels")),
        api_url=_parse_api_url(config.get("github")),
    )


def _parse_repository(raw_repository: object) -> RepositorySpec | None:
    if raw_repository is None:
        return None

    repository_table = _required_table(raw_repository, "[repository]")
    owner = _required_string(repository_table, "owner", "[repository]")
    name = _required_string(repository_table, "name", "[repository]")
    return RepositorySpec(owner=owner, name=name)


def _parse_api_url(raw_github: object) -> str | None:
    if raw_github is None:
        return None

    github_table = _required_table(raw_github, "[github]")
    raw_api_url = github_table.get("api_url")
    if raw_api_url is None:
        return None
    if not isinstance(raw_api_url, str):
        msg = "github.api_url must be a non-empty string when provided"
        raise ConfigError(msg)
    normalized = raw_api_url.strip().rstrip("/")
    if not normalized:
        msg = "github.api_url must be a non-empty string when provided"
        raise ConfigError(msg)
    return normalized


def _parse_labels(raw_labels: object) -> tuple[LabelSpec, ...]:
    if raw_labels is None:
        return ()
    if not isinstance(raw_labels, list):
        msg = "The labels key must be an array of TOML tables"
        raise ConfigError(msg)

    labels = tuple(_parse_label(raw_label) for raw_label in raw_labels)
    _reject_duplicate_labels(labels)
    return labels


def _parse_label(raw_label: object) -> LabelSpec:
    label_table = _required_table(raw_label, "[[labels]]")

    description = label_table.get("description")
    if description is not None and not isinstance(description, str):
        msg = "label.description must be a string when provided"
        raise ConfigError(msg)

    raw_color = label_table.get("color", DEFAULT_COLOR)
    if not isinstance(raw_color, str):
        msg = "label.color must be a string when provided"
        raise ConfigError(msg)

    return LabelSpec(
        name=_required_string(label_table, "name", "[[labels]]"),
        color=raw_color,
        description=description,
    )


def _required_table(value: object, context: str) -> cabc.Mapping[str, typ.Any]:
    if not isinstance(value, cabc.Mapping):
        msg = f"The {context} table must be a TOML table"
        raise ConfigError(msg)
    return typ.cast("cabc.Mapping[str, typ.Any]", value)


def _required_string(
    values: cabc.Mapping[str, typ.Any],
    key: str,
    context: str,
) -> str:
    raw_value = values.get(key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        msg = f"{context}.{key} must be a non-empty string"
        raise ConfigError(msg)
    return raw_value.strip()


def _reject_duplicate_labels(labels: tuple[LabelSpec, ...]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for label in labels:
        key = label.name.casefold()
        if key in seen:
            duplicates.add(label.name)
        seen.add(key)

    if duplicates:
        duplicate_names = ", ".join(sorted(duplicates))
        msg = f"Duplicate label definitions: {duplicate_names}"
        raise ConfigError(msg)
