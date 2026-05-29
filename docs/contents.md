# Documentation contents

This page is the index for project documentation. Use it to find the
maintainer-facing guide, user-facing guide, style rules, and operational
reference material.

## Core guides

- [Users' guide](users-guide.md): command usage, configuration files,
  repository selection, authentication, GitHub Enterprise and simulator usage,
  TOML label configuration, default labels, and local quality gates.
- [Developers' guide](developers-guide.md): package architecture, module
  organization, data flow, normalization rules, testing strategy, and local
  development workflow.
- [Repository layout](repository-layout.md): top-level directories and files,
  package modules, tests, generated artefacts, and maintenance expectations.

## Standards and references

- [Documentation style guide](documentation-style-guide.md): spelling,
  Markdown, diagram, roadmap, and Architectural Decision Record (ADR)
  conventions.
- [Scripting standards](scripting-standards.md): robust scripting practices
  for automation and maintenance scripts.
- [Local validation of GitHub Actions with act and pytest](local-validation-of-github-actions-with-act-and-pytest.md):
  guidance for validating workflow behaviour locally.

## Documentation maintenance

When adding or changing a feature, update the relevant guide in the same
change. User-facing behaviour belongs in the users' guide. Internal
architecture, conventions, and test strategy belong in the developers' guide or
repository layout document. Substantive decisions should be recorded in an ADR
and referenced from the relevant design document.
