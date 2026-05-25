# create-labels developers' guide

This guide summarises the package structure, internal boundaries, and local
development workflow for maintainers.

## Architecture

`create-labels` has three small runtime layers:

- `create_labels.config` owns the TOML parsing boundary. It converts raw data
  into `RepositorySpec`, `LabelSpec`, and `LabelConfig`, normalizes label
  colours and descriptions, and raises `ConfigError` before any network call is
  attempted.
- `create_labels.sync` owns the domain sync decision. It works against
  protocol-shaped repository and label objects, so unit tests can use simple
  fakes while the GitHub adapter supplies real `github3.py` objects.
- `create_labels.github` owns GitHub integration. It resolves repository,
  token, and API URL inputs, creates the GitHub client, fetches the repository,
  selects configured labels or `DEFAULT_LABELS`, and delegates mutation
  decisions to `sync_labels`.

The command-line layer in `create_labels.cli` wires Cyclopts arguments into the
configuration and GitHub integration layers. It is intentionally thin so
behaviour remains testable through `load_config`, `sync_labels`, and
`sync_repository_labels`.

## Data flow

The normal execution path is:

1. `cli.main` receives `--config`, `--repository`, `--token`, and `--api-url`.
2. `load_config` parses TOML into a `LabelConfig`, or `cli.main` creates an
   empty `LabelConfig` so the imported defaults apply.
3. `sync_repository_labels` resolves repository coordinates and authentication
   from explicit arguments, configuration, and environment variables.
4. `sync_labels` looks up each desired label, creates missing labels, updates
   changed labels, and returns `LabelSyncResult` values.

`sync_labels` never deletes labels that are absent from the desired
configuration. Existing label names are URL-encoded for github3.py lookup, but
create and update payloads keep the raw GitHub label name.

## Normalization rules

`LabelSpec` is the source of truth for desired label normalization:

- label names are stripped and must be non-empty;
- colours may include a leading `#`, are uppercased, and must be six
  hexadecimal characters;
- descriptions are stripped when present and remain `None` when omitted.

Remote GitHub labels are normalized to the same shape before sync compares them
with `LabelSpec`. This keeps repeated runs idempotent when GitHub returns
lowercase colours, a leading `#`, padded descriptions, or null descriptions.

## Testing strategy

The test suite has three levels:

- unit tests cover configuration parsing, CLI wiring, and sync decisions using
  in-memory fakes;
- behaviour tests in `tests/steps` exercise create/update scenarios through
  pytest-bdd;
- the Betamax test records github3.py request behaviour against a local
  GitHub-shaped HTTP server.

Prefer focused unit tests for parser and sync changes. Add behaviour coverage
when a change affects user-visible workflows.

## Local workflow

Use Makefile targets for validation:

```bash
make fmt
make check-fmt
make markdownlint
make nixie
make typecheck
make lint
make test
```

Run the same gates before committing. The Makefile provisions the virtual
environment through `uv` and runs pytest with the configured worker count.
