"""github3.py integration tests recorded through Betamax."""

from __future__ import annotations

import json
import pathlib
import threading
import typing as typ
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import github3
from betamax import Betamax
from github3.session import GitHubSession

from create_labels.config import LabelSpec
from create_labels.github import _GitHubRepositoryAdapter
from create_labels.sync import LabelSyncResult, sync_labels

_PAYLOAD_FIXTURE = (
    pathlib.Path(__file__).parent / "fixtures" / "repository_payload.json"
)


class LabelApiHandler(BaseHTTPRequestHandler):
    """Minimal GitHub API mock used for Betamax integration tests.

    The handler implements repository lookup plus label GET, PATCH, and POST
    endpoints. It records all ``(method, path)`` pairs in ``requests`` for
    assertions and returns JSON payloads shaped for github3.py. It is not a
    general GitHub API simulator.
    """

    requests: typ.ClassVar[list[tuple[str, str]]]
    request_lock: typ.ClassVar[threading.Lock]

    def do_GET(self) -> None:
        """Serve repository lookup and existing-label lookup."""
        self._record_request("GET")
        if self.path == "/repos/octocat/hello-world":
            self._send_json(200, self._repository_payload())
            return

        label_name = _label_name_from_path(self.path)
        if label_name == "risk: low":
            self._send_json(200, self._label_payload(label_name, "FFFFFF", None))
            return

        self._send_json(404, {"message": "Not Found"})

    def do_PATCH(self) -> None:
        """Serve label updates."""
        self._record_request("PATCH")
        request = self._read_json()
        self._send_json(
            200,
            self._label_payload(
                str(request["name"]),
                str(request["color"]),
                typ.cast("str | None", request.get("description")),
            ),
        )

    def do_POST(self) -> None:
        """Serve label creation."""
        self._record_request("POST")
        request = self._read_json()
        self._send_json(
            201,
            self._label_payload(
                str(request["name"]),
                str(request["color"]),
                typ.cast("str | None", request.get("description")),
            ),
        )

    def log_message(
        self,
        format: str,  # noqa: A002 - BaseHTTPRequestHandler interface contract.
        *args: object,
    ) -> None:
        """Silence request logs during tests."""

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length)
        return typ.cast("dict[str, object]", json.loads(raw_body.decode("utf-8")))

    def _record_request(self, method: str) -> None:
        with self.request_lock:
            self.requests.append((method, self.path))

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _repository_payload(self) -> dict[str, object]:
        base_url = self._base_url()
        repo_url = f"{base_url}/repos/octocat/hello-world"
        raw_payload = _PAYLOAD_FIXTURE.read_text(encoding="utf-8")
        payload = typ.cast("dict[str, object]", json.loads(raw_payload))
        return _replace_payload_urls(payload, base_url=base_url, repo_url=repo_url)

    def _label_payload(
        self,
        name: str,
        color: str,
        description: str | None,
    ) -> dict[str, object]:
        return {
            "id": abs(hash(name)) % 100_000,
            "name": name,
            "color": color,
            "description": description,
            "url": f"{self._base_url()}/repos/octocat/hello-world/labels/{name}",
        }

    def _base_url(self) -> str:
        server = typ.cast("ThreadingHTTPServer", self.server)
        return f"http://127.0.0.1:{server.server_port}"


def test_sync_labels_uses_github3_requests_recorded_by_betamax(
    tmp_path: pathlib.Path,
) -> None:
    """Betamax records github3.py HTTP calls against a GitHub-shaped API."""
    LabelApiHandler.requests = []
    LabelApiHandler.request_lock = threading.Lock()
    server = ThreadingHTTPServer(("127.0.0.1", 0), LabelApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        results = _sync_with_betamax(server.server_port, tmp_path)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert results == (
        LabelSyncResult("risk: low", "updated"),
        LabelSyncResult("risk: high", "created"),
    )
    with LabelApiHandler.request_lock:
        recorded = list(LabelApiHandler.requests)
    assert (
        "PATCH",
        "/repos/octocat/hello-world/labels/risk:%20low",
    ) in recorded
    assert ("POST", "/repos/octocat/hello-world/labels") in recorded


def _sync_with_betamax(
    port: int,
    cassette_directory: pathlib.Path,
) -> tuple[LabelSyncResult, ...]:
    """Record github3.py HTTP traffic through Betamax and return sync results."""
    session = GitHubSession()
    session.base_url = f"http://127.0.0.1:{port}"
    auth_value = "sample-auth-value"

    recorder = Betamax(session, cassette_library_dir=str(cassette_directory))
    with recorder.use_cassette("github-label-sync", record="all"):
        github = github3.GitHub(token=auth_value, session=session)
        repository = github.repository("octocat", "hello-world")
        assert repository is not None
        return sync_labels(
            _GitHubRepositoryAdapter(repository),
            (
                LabelSpec("risk: low", "4CAF50", "Low risk"),
                LabelSpec("risk: high", "F44336", "High risk"),
            ),
        )


def _label_name_from_path(path: str) -> str | None:
    """Extract URL-decoded label name from GitHub API path, or None."""
    label_path = "/repos/octocat/hello-world/labels/"
    if not path.startswith(label_path):
        return None
    return urllib.parse.unquote(path.removeprefix(label_path))


def _replace_payload_urls(
    value: object,
    *,
    base_url: str,
    repo_url: str,
) -> dict[str, object]:
    replaced = _replace_placeholders(value, base_url=base_url, repo_url=repo_url)
    return typ.cast("dict[str, object]", replaced)


def _replace_placeholders(value: object, *, base_url: str, repo_url: str) -> object:
    if isinstance(value, str):
        return value.replace("__BASE_URL__", base_url).replace("__REPO_URL__", repo_url)
    if isinstance(value, list):
        return [
            _replace_placeholders(item, base_url=base_url, repo_url=repo_url)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _replace_placeholders(item, base_url=base_url, repo_url=repo_url)
            for key, item in value.items()
        }
    return value
