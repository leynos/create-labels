"""Contract tests for main-owned Python coverage publication."""

from __future__ import annotations

import typing as typ
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
COVERAGE_WORKFLOW = ROOT / ".github" / "workflows" / "coverage-main.yml"
GENERATE_COVERAGE_ACTION = (
    "leynos/shared-actions/.github/actions/generate-coverage"
    "@152d9c4784d0ae5877938a984fe6d1f04d718fd8"
)
UPLOAD_COVERAGE_ACTION = (
    "leynos/shared-actions/.github/actions/upload-codescene-coverage"
    "@152d9c4784d0ae5877938a984fe6d1f04d718fd8"
)


def _load(path: Path) -> dict[str, object]:
    """Load a workflow mapping from ``path``."""
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), f"{path} must contain a mapping"
    return typ.cast("dict[str, object]", workflow)


def _triggers(workflow: dict[str, object]) -> dict[str, object]:
    """Return a workflow's trigger mapping."""
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict), "workflow must declare an on: mapping"
    return typ.cast("dict[str, object]", triggers)


def _job(workflow: dict[str, object], name: str) -> dict[str, object]:
    """Return the named job from ``workflow``."""
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "workflow must declare a jobs mapping"
    job = jobs.get(name)
    assert isinstance(job, dict), f"workflow job {name!r} must be a mapping"
    return typ.cast("dict[str, object]", job)


def _steps(job: dict[str, object]) -> list[dict[str, object]]:
    """Return the mapping steps declared by ``job``."""
    steps = job.get("steps")
    assert isinstance(steps, list), "workflow job must declare a steps list"
    assert all(isinstance(step, dict) for step in steps), (
        "workflow steps must be mappings"
    )
    return typ.cast("list[dict[str, object]]", steps)


def _step(job: dict[str, object], name: str) -> dict[str, object]:
    """Return the named step from ``job``."""
    step = next(
        (candidate for candidate in _steps(job) if candidate.get("name") == name),
        None,
    )
    assert step is not None, f"workflow step {name!r} is missing"
    return step


def _with(step: dict[str, object]) -> dict[str, object]:
    """Return a step's input mapping."""
    values = step.get("with")
    assert isinstance(values, dict), "coverage step must declare a with: mapping"
    return typ.cast("dict[str, object]", values)


def test_pull_request_coverage_is_local_serial_ratchet() -> None:
    """Keep pull-request coverage local and independent of CodeScene."""
    workflow = _load(CI_WORKFLOW)
    source = CI_WORKFLOW.read_text(encoding="utf-8")
    job = _job(workflow, "lint-test")
    checkout = _step(job, "Check out repository")
    checkout_with = typ.cast("dict[str, object]", checkout.get("with") or {})
    assert checkout_with.get("fetch-depth") != 0
    assert "CS_ACCESS_TOKEN" not in source
    assert "codescene" not in source.lower()

    coverage = _step(job, "Test and Measure Coverage")
    assert coverage.get("if") == "github.event_name == 'pull_request'"
    assert coverage.get("uses") == GENERATE_COVERAGE_ACTION
    assert _with(coverage) == {
        "language": "python",
        "output-path": "coverage.xml",
        "format": "cobertura",
        "python-source": "create_labels",
        "baseline-python-file": ".coverage-baseline.python",
        "pytest-workers": "",
        "with-ratchet": "true",
    }
    assert not any(
        "upload-codescene-coverage" in str(step.get("uses", ""))
        or "cs-coverage" in str(step.get("run", ""))
        for step in _steps(job)
    )


def test_main_coverage_publishes_the_ratchet_baseline() -> None:
    """Keep CodeScene publication restricted to pushes on main."""
    workflow = _load(COVERAGE_WORKFLOW)
    assert _triggers(workflow) == {"push": {"branches": ["main"]}}
    job = _job(workflow, "coverage-upload")
    env = job.get("env")
    assert isinstance(env, dict), "main coverage job must own its environment"
    assert "CS_ACCESS_TOKEN" in env
    coverage = _step(job, "Generate coverage")
    assert coverage.get("uses") == GENERATE_COVERAGE_ACTION
    assert _with(coverage) == {
        "language": "python",
        "output-path": "coverage.xml",
        "format": "cobertura",
        "python-source": "create_labels",
        "baseline-python-file": ".coverage-baseline.python",
        "pytest-workers": "",
        "with-ratchet": "true",
    }
    upload = _step(job, "Upload coverage data to CodeScene")
    assert upload.get("uses") == UPLOAD_COVERAGE_ACTION
    assert _with(upload)["mode"] == "upload"
