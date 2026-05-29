# Repository layout

This document describes the repository structure for maintainers. It explains
where runtime code, tests, documentation, and validation configuration live.

## Top-level files

- `AGENTS.md`: agent instructions for coding, testing, documentation, and
  quality gates in this repository.
- `README.md`: public project overview, quick-start commands, and links to the
  users' and developers' guides.
- `Makefile`: canonical local validation entrypoint. Prefer Make targets over
  invoking tools directly.
- `pyproject.toml`: Python package metadata, dependency groups, and tool
  configuration.
- `uv.lock`: locked Python dependency graph for reproducible development
  environments.

## Runtime package

Runtime code lives under `create_labels/`:

- `__init__.py`: public import boundary for library consumers.
- `cli.py`: Cyclopts command-line entrypoint and argument wiring.
- `config.py`: TOML parsing, validation, and typed configuration values.
- `defaults.py`: built-in default label set.
- `github.py`: github3.py integration, repository resolution, authentication,
  and adapter behaviour.
- `sync.py`: vendor-neutral label synchronization decisions over repository
  and label protocols.

Keep parsing, GitHub integration, defaults, and sync decisions in their
existing modules unless a change needs a new boundary. The sync module should
remain independent of github3.py-specific exceptions and transport behaviour.

## Tests

Tests live under `tests/`:

- `test_config.py`: configuration parsing and default-label regression tests.
- `test_cli.py`: command wiring and CLI output tests.
- `test_github.py`: GitHub adapter error-path tests.
- `test_github_betamax.py`: github3.py integration behaviour recorded through
  Betamax against a local GitHub-shaped HTTP server.
- `test_sync.py`: unit tests for label synchronization decisions.
- `steps/`: pytest-bdd step definitions for behavioural scenarios.
- `features/`: Gherkin feature files consumed by pytest-bdd.
- `fixtures/`: JSON and other reusable test fixtures.

Prefer focused unit tests for parser and sync changes. Add behavioural tests
when a change affects user-visible workflows. Add integration tests when a
change affects GitHub API contracts, command-line behaviour, or another
externally observable boundary.

## Documentation

Documentation lives under `docs/`:

- `contents.md`: documentation index.
- `users-guide.md`: user-facing command and configuration guidance.
- `developers-guide.md`: maintainer-facing architecture and workflow guidance.
- `repository-layout.md`: this repository structure reference.
- `documentation-style-guide.md`: documentation writing and ADR conventions.
- `scripting-standards.md`: standards for scripts and automation.
- `local-validation-of-github-actions-with-act-and-pytest.md`: local workflow
  validation guidance.

Update documentation with the code change that makes it necessary. Behaviour
changes belong in the users' guide; internal interfaces and conventions belong
in the developers' guide or this layout reference.

## Generated and local artefacts

The following paths are local or generated and should not be treated as source
design inputs:

- `.venv/`: local virtual environment managed by `uv`.
- `.uv-cache/` and `.uv-tools/`: local `uv` cache and tool directories.
- `.pytest_cache/`: pytest cache.
- `__pycache__/`: Python bytecode cache directories.

Use `make clean` to remove common generated artefacts when needed.
