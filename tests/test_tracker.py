import io
import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.shared.contracts import Incident, IncidentSeverity, IncidentStatus
from app.swe.dispatch import DevinDispatcher
from app.swe.tracker import IssueTracker


def _incident() -> Incident:
    return Incident(
        id=uuid4(),
        service="yuki-core-api",
        summary="500s on /health",
        severity=IncidentSeverity.P1,
        status=IncidentStatus.OPEN,
        source="presence_poller",
    )


def _resp(payload: dict) -> MagicMock:
    m = MagicMock()
    m.read.return_value = json.dumps(payload).encode()
    m.__enter__ = lambda s: s
    m.__exit__ = lambda *a: None
    return m


def test_code_level_creates_both() -> None:
    tracker = IssueTracker("lin-key", "team-1", "gh-pat", "owner/repo")
    with patch("app.swe.tracker.urllib.request.urlopen") as urlopen:
        urlopen.side_effect = [
            _resp({"data": {"issueCreate": {"success": True, "issue": {"identifier": "POC-1", "url": "https://linear.app/x/POC-1"}}}}),
            _resp({"number": 42, "html_url": "https://github.com/owner/repo/issues/42"}),
        ]
        refs = tracker.create_issue(_incident(), "ctx", code_level=True)
    assert refs["linear_url"] == "https://linear.app/x/POC-1"
    assert refs["github_url"] == "https://github.com/owner/repo/issues/42"


def test_infra_only_goes_linear_only() -> None:
    tracker = IssueTracker("lin-key", "team-1", "gh-pat", "owner/repo")
    with patch("app.swe.tracker.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _resp(
            {"data": {"issueCreate": {"success": True, "issue": {"identifier": "POC-2", "url": "https://linear.app/x/POC-2"}}}}
        )
        refs = tracker.create_issue(_incident(), "ctx", code_level=False)
    assert "linear_url" in refs
    assert "github_url" not in refs


def test_unconfigured_degrades_gracefully() -> None:
    tracker = IssueTracker(None, None, None, None)
    refs = tracker.create_issue(_incident(), "ctx", code_level=True)
    assert "linear_url" not in refs and "github_url" not in refs


def test_pr_status_parsing() -> None:
    tracker = IssueTracker(None, None, "gh-pat", "owner/repo")
    with patch("app.swe.tracker.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _resp({"state": "closed", "merged": True, "merged_by": {"login": "ivin-titus"}})
        status = tracker.pr_status("https://github.com/owner/repo/pull/7")
    assert status["merged"] is True
    assert status["merged_by"] == "ivin-titus"


def test_linear_error_surfaces_not_crashes() -> None:
    tracker = IssueTracker("lin-key", "team-1", None, None)
    with patch("app.swe.tracker.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _resp({"errors": [{"message": "Unauthorized"}]})
        refs = tracker.create_issue(_incident(), "ctx", code_level=False)
    assert refs["linear_error"] == "Unauthorized"


def test_dispatcher_session_pull_requests() -> None:
    dispatcher = DevinDispatcher("devin-key")
    payload = {"pull_requests": [{"url": "https://github.com/owner/repo/pull/9"}]}
    with patch("app.swe.dispatch.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _resp(payload)
        prs = dispatcher.session_pull_requests("sess-1")
    assert prs == ["https://github.com/owner/repo/pull/9"]


def test_dispatcher_session_pull_requests_no_key() -> None:
    dispatcher = DevinDispatcher(None)
    assert dispatcher.session_pull_requests("sess-1") == []
