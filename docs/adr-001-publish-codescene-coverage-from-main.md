# Architectural decision record (ADR) 001: Publish CodeScene coverage from main

## Status

Accepted (2026-09-24): coverage is uploaded to CodeScene only by
`coverage-main.yml` on `main`; pull-request lanes ratchet locally and never
contact CodeScene.

## Date

2026-09-24.

## Context and problem statement

Pull-request continuous integration (CI) used to generate coverage and send it
to CodeScene from the same lane, which put `CS_ACCESS_TOKEN` and a call to
CodeScene's application programming interface (API) on every pull request. The
cs-coverage client refuses to run when that API changes shape, which has
happened twice, and each time it held every open pull request red for a reason
unrelated to the change under review. The token was also in reach of any
workflow a pull request could start.

The question was where coverage should be published, and how the pull-request
ratchet should keep a baseline to compare against once the lanes no longer
publish.

## Decision drivers

- A change in CodeScene's API must not hold a pull request.
- No workflow a pull request can start may hold `CS_ACCESS_TOKEN` or name
  CodeScene.
- The pull-request ratchet must compare against a baseline measured the same
  way, with the same inputs at the same `shared-actions` pin.
- There must be exactly one baseline writer, so that two runs cannot race to
  write it.

## Options considered

### Option A: Keep the upload in the pull-request lane

The lane keeps working as before. Every pull request still depends on
CodeScene's API and holds the token.

### Option B: One push-to-main publisher

A separate workflow, `coverage-main.yml`, generates coverage on each push to
`main`, writes the ratchet baseline, and uploads the report. Pull-request lanes
generate coverage with the ratchet on and publish nothing.

| Topic                          | Option A      | Option B            |
| ------------------------------ | ------------- | ------------------- |
| CodeScene API on the PR path   | Yes           | No                  |
| Token in pull-request reach    | Yes           | No                  |
| Baseline writers               | Every lane    | The publisher alone |
| Coverage seen by CodeScene     | Every head    | Each `main` commit  |

_Table 1: Trade-offs between publishing from pull requests and from main._

## Decision outcome / proposed direction

Option B. `coverage-main.yml` is the only publisher and the only baseline
writer. It also answers `workflow_dispatch`, for merges that fire no push
event. Its upload step runs only when a check step reports that the token is
set and the ref is `refs/heads/main`, and it receives the token only as the
uploader's `access-token` input, never through an `env` block.

A dispatch cannot advance the baseline. The shared coverage action writes it
only on a push to `main` when `publish-baseline` is `auto`. Setting `always`
would hand that restriction to the calling workflow, and on a pull-request lane
each push could then lower the baseline its next push ratchets against, so the
contract refuses any value but `auto`. A dispatch on `main` therefore uploads a
fresh report while the ratchet catches up at the next push.

The contract tests under `tests/` hold this shape, and every clause is proved
by a mutation that the clause refuses. The
[developers' guide](developers-guide.md#coverage-workflow-contract) describes
the resulting workflow shape.

## Known risks and limitations

- Merges made by the Dependabot automerge workflow use `GITHUB_TOKEN` and fire
  no push, so they are measured only at the next push or a manual dispatch.
  The fix belongs in the shared automerge workflow and is tracked in
  leynos/shared-actions#518.
- A dispatch that replaces a pending push leaves the baseline one commit behind
  until the next push, also tracked in leynos/shared-actions#518.
- A repository-scoped secret can still be read by a write-access user who adds
  a push- or dispatch-triggered workflow on a branch. Only a `main`-restricted
  environment closes that path, and adopting one is the repository owner's
  decision.
