"""Default labels imported from the original shell script.

``DEFAULT_LABELS`` is the complete label set applied when a TOML configuration
does not provide any ``[[labels]]`` entries. The imported groups cover pull
request size, risk, code scope, workflow exceptions, and contributor history.
"""

from __future__ import annotations

from .config import LabelSpec

DEFAULT_LABELS: tuple[LabelSpec, ...] = (
    LabelSpec("size: XS", "F9D0C4", "< 10 changed lines (excluding docs)"),
    LabelSpec("size: S", "F5A3A3", "10-49 changed lines"),
    LabelSpec("size: M", "E57373", "50-199 changed lines"),
    LabelSpec("size: L", "D32F2F", "200-499 changed lines"),
    LabelSpec("size: XL", "B71C1C", "500+ changed lines"),
    LabelSpec("risk: low", "4CAF50", "Changes to docs, tests, or low-risk modules"),
    LabelSpec(
        "risk: medium", "FFC107", "Business logic, config, or moderate-risk modules"
    ),
    LabelSpec(
        "risk: high", "F44336", "Safety, secrets, auth, or critical infrastructure"
    ),
    LabelSpec(
        "risk: manual", "9E9E9E", "Risk level set manually (sticky, not overwritten)"
    ),
    LabelSpec("scope: agent", "006B75", "Agent core (agent loop, router, scheduler)"),
    LabelSpec("scope: channel", "00838F", "Channel infrastructure"),
    LabelSpec("scope: channel/cli", "00897B", "TUI / CLI channel"),
    LabelSpec("scope: channel/web", "00796B", "Web gateway channel"),
    LabelSpec("scope: channel/wasm", "00695C", "WASM channel runtime"),
    LabelSpec("scope: tool", "1565C0", "Tool infrastructure"),
    LabelSpec("scope: tool/builtin", "1976D2", "Built-in tools"),
    LabelSpec("scope: tool/wasm", "1E88E5", "WASM tool sandbox"),
    LabelSpec("scope: tool/mcp", "2196F3", "MCP client"),
    LabelSpec("scope: tool/builder", "42A5F5", "Dynamic tool builder"),
    LabelSpec("scope: db", "4A148C", "Database trait / abstraction"),
    LabelSpec("scope: db/postgres", "6A1B9A", "PostgreSQL backend"),
    LabelSpec("scope: db/libsql", "7B1FA2", "libSQL / Turso backend"),
    LabelSpec("scope: safety", "880E4F", "Prompt injection defense"),
    LabelSpec("scope: llm", "4527A0", "LLM integration"),
    LabelSpec("scope: workspace", "283593", "Persistent memory / workspace"),
    LabelSpec("scope: orchestrator", "0D47A1", "Container orchestrator"),
    LabelSpec("scope: worker", "01579B", "Container worker"),
    LabelSpec("scope: secrets", "BF360C", "Secrets management"),
    LabelSpec("scope: config", "E65100", "Configuration"),
    LabelSpec("scope: extensions", "33691E", "Extension management"),
    LabelSpec("scope: setup", "827717", "Onboarding / setup"),
    LabelSpec("scope: evaluation", "558B2F", "Success evaluation"),
    LabelSpec("scope: estimation", "9E9D24", "Cost/time estimation"),
    LabelSpec("scope: sandbox", "00BFA5", "Docker sandbox"),
    LabelSpec("scope: hooks", "6D4C41", "Git/event hooks"),
    LabelSpec("scope: pairing", "4E342E", "Pairing mode"),
    LabelSpec("scope: ci", "546E7A", "CI/CD workflows"),
    LabelSpec("scope: docs", "78909C", "Documentation"),
    LabelSpec("scope: dependencies", "90A4AE", "Dependency updates"),
    LabelSpec(
        "dependencies",
        "0366D6",
        "Dependency updates and dependency manager pull requests",
    ),
    LabelSpec("github-actions", "2088FF", "GitHub Actions workflow updates"),
    LabelSpec("cargo", "DEA584", "Rust Cargo package and lockfile updates"),
    LabelSpec(
        "skip-regression-check",
        "9E9E9E",
        "Acknowledged: fix without regression test",
    ),
    LabelSpec("contributor: new", "FFF9C4", "First-time contributor"),
    LabelSpec("contributor: regular", "FFE082", "2-5 merged PRs"),
    LabelSpec("contributor: experienced", "FFB74D", "6-19 merged PRs"),
    LabelSpec("contributor: core", "FF8A65", "20+ merged PRs"),
)
