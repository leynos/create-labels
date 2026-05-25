# create-labels Users' Guide

`create-labels` creates and updates GitHub repository labels from a TOML
configuration file. When no labels are provided in configuration, it applies
the default label set imported from Axinite's
`.github/scripts/create-labels.sh` script.

## Command

Install the package and run the console script:

```bash
create-labels --repository owner/repo --token "$GITHUB_TOKEN"
```

The command uses `github3.py` for GitHub API access. It does not shell out to
the GitHub CLI.

## Repository Selection

The target repository can be supplied in three ways, in priority order:

- `--repository owner/repo`;
- `[repository]` in the TOML file; or
- the `GITHUB_REPOSITORY` environment variable.

## Authentication

Pass a token with `--token`, or set `GITHUB_TOKEN` in the environment:

```bash
GITHUB_TOKEN=ghp_example create-labels --repository owner/repo
```

## GitHub Enterprise and Simulators

Use `--api-url` to target GitHub Enterprise or a local GitHub API simulator:

```bash
create-labels --repository owner/repo --api-url http://127.0.0.1:3000
```

The same value can be stored as `github.api_url` in TOML.

## TOML Configuration

Each label must have a `name`. `color` and `description` are optional. Colours
may include a leading `#`; they are normalised to the six-character hex form
expected by GitHub.

```toml
[repository]
owner = "leynos"
name = "example"

[github]
api_url = "https://api.github.com"

[[labels]]
name = "risk: low"
color = "4CAF50"
description = "Changes to docs, tests, or low-risk modules"

[[labels]]
name = "needs-review"
```

Labels omitted from the file are not deleted from GitHub. The tool only creates
missing labels and updates labels named in the effective configuration.

## Default Labels

If the TOML file contains no `[[labels]]` entries, the imported Axinite label
set is used. It includes:

- size labels;
- risk labels;
- scope labels;
- workflow labels; and
- contributor labels.

## Local Quality Gates

Use the Makefile targets for local validation:

```bash
make check-fmt
make typecheck
make lint
make test
```

`make test` runs the unit tests and pytest-bdd behavioural scenarios.
