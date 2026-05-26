# create-labels

`create-labels` creates and updates GitHub repository labels from a TOML
configuration file or from the built-in df12 label set. It is a small Python
command-line tool for making label setup repeatable across repositories without
shelling out to the GitHub CLI.

## Why use this?

- Apply a consistent default label set to new repositories.
- Keep repository labels in sync from reviewed TOML configuration.
- Support GitHub Enterprise and local API simulators through `--api-url`.
- Avoid deleting labels that are outwith the desired configuration.

## Quick start

Install the package, provide a token, and choose a target repository:

```bash
create-labels --repository owner/repo --token "$GITHUB_TOKEN"
```

To use a TOML configuration file:

```bash
create-labels --config labels.toml --repository owner/repo
```

When no labels are provided in TOML, the built-in default labels are applied.

## Documentation

Read the [users' guide](docs/users-guide.md) for command-line options,
configuration format, GitHub Enterprise usage, and local validation commands.

Read the [developers' guide](docs/developers-guide.md) for package boundaries,
data flow, normalization rules, and testing strategy.

## Compatibility note

This package is no longer the Copier template placeholder project. The old
sample `hello` function has been removed; use the `create-labels` console
script or the public exports from `create_labels` instead.
