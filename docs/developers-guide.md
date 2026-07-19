# create-labels developers' guide

This guide summarizes the package structure, internal boundaries, and local
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

## Mutation-testing workflow contract tests

This repository runs scheduled, informational mutation testing through a thin
caller workflow,
[`.github/workflows/mutation-testing.yml`](../.github/workflows/mutation-testing.yml),
which delegates to the shared reusable workflow
`leynos/shared-actions/.github/workflows/mutation-mutmut.yml`. The heavy
lifting — running `mutmut`, and summarizing survivors — lives in
`shared-actions`; this repository carries only declarative configuration. The
run is **informational only**: it never gates a pull request. Survivors are
reported through the job summary and downloadable artefacts so they can be
triaged into tests, not enforced as a blocking check. The mutation targets and
test selection themselves are configured in `[tool.mutmut]` in `pyproject.toml`
(`source_paths`, `pytest_add_cli_args_test_selection`).

The workflow runs in two modes. A **daily schedule** fires a change-scoped run
that mutates only the source files touched within the detection window, so
quiet days are cheap no-ops. A **manual dispatch** (the Actions "Run workflow"
control) mutates the whole package; select a branch in that control to exercise
a feature branch.

The caller passes the flat-layout configuration this package needs:

- `paths` — set to `create_labels/`, the change-detection glob that decides
  whether a scheduled run has anything to mutate.
- `module-prefix-strip` — set to an empty string, because the mutable source
  lives directly under `create_labels/` rather than under a `src/` prefix.

The `uses:` reference pins the shared workflow to a full 40-character commit
SHA rather than a branch or tag, so a force-push upstream cannot silently
change what runs here. The contract test hard-codes the expected SHA in a
`PINNED_SHA` constant and asserts the `uses:` line matches it, so bumping the
pin means editing the workflow's `uses:` line and that constant together in the
same change.

Because the caller is configuration rather than code, a contract test in
`tests/test_workflow_contract.py` pins the shape it must uphold, failing the
pull request when the caller drifts — repointing the pin at a branch, widening
the token scope, or dropping a configuration input — rather than letting the
breakage surface only in a scheduled run. The test module self-skips when the
workflow file is absent (mutmut copies the sources into a sandbox that omits
`.github/`, so the contract test does not run there). Run it locally with:

```bash
uv run --with pytest --with pyyaml pytest tests/test_workflow_contract.py -q
```

The test validates:

- the `uses:` reference targets `mutation-mutmut.yml` pinned to the documented
  commit SHA;
- the `with:` block carries exactly `paths` and `module-prefix-strip`, the
  flat-layout configuration above;
- job permissions are least-privilege (`contents: read`, `id-token: write`)
  and the workflow-level default token scope is empty;
- `concurrency` serializes runs per ref without cancelling one in progress;
  and
- the triggers keep the daily schedule and a plain `workflow_dispatch` with no
  inputs.

## Local workflow

Use Makefile targets for validation:

```bash
make fmt
make check-fmt
make markdownlint
make spelling
make nixie
make typecheck
make lint
make test
```

Run the same gates before committing. The Makefile provisions the virtual
environment through `uv` and runs pytest with the configured worker count.

The spelling gate refreshes the shared en-GB-oxendict dictionary into an
untracked local cache only when the authoritative copy is newer, merges the
repository-specific policy in `typos.local.toml`, and regenerates the tracked
`typos.toml`. Edit the local policy rather than the generated configuration.

## Workflow pins and Dependabot

Dependabot owns the upgrade of GitHub Actions and reusable workflows,
including calls into `leynos/shared-actions`. Contract tests that assert a
caller's exact commit SHA create a lockstep dependency: every time Dependabot
opens a bump PR, the test fails until a human edits the pinned constant to
match. That defeats the purpose of automated dependency updates and turns a
routine bump into a manual chore.

Contract tests may still verify the *shape* of a reusable-workflow caller.
They must not verify the specific SHA value.

- Do assert the workflow references the correct reusable workflow path.
- Do assert the ref is pinned to a full 40-character commit SHA, not a
  mutable branch such as `main` or `rolling`.
- Do assert the expected `on:` triggers, least-privilege `permissions:`, and
  the inputs the caller relies on.
- Do not hard-code the current SHA value as an expected string. Match it with
  a pattern instead.
- Do not fail a test purely because Dependabot bumped the pinned SHA.

```python
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def test_uses_pinned_full_sha(caller_step):
    ref = caller_step["uses"].split("@")[-1]
    assert SHA_RE.match(ref), f"expected a 40-hex commit SHA, got {ref!r}"
```

If a workflow's behaviour genuinely depends on a feature only present from a
particular commit onwards, express that as a comment or a changelog note, not
as a test assertion on the SHA string.
