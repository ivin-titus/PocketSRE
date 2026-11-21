"""Issue tracking + PR link-back (PRD §4.6 / §5).

Split decided with the owner: code-level incidents land on BOTH GitHub Issues
and Linear; infra-only incidents go to Linear only. PocketSRE never merges —
it creates, links, polls, and reports.
"""

import json
import urllib.request
from urllib.error import HTTPError, URLError
from uuid import UUID

from app.shared.contracts import Incident


def _post(url: str, payload: dict, headers: dict[str, str], timeout: float) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get(url: str, headers: dict[str, str], timeout: float) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class IssueTracker:
    """Linear (GraphQL) + GitHub Issues dual tracking; each leg degrades gracefully."""

    def __init__(
        self,
        linear_api_key: str | None,
        linear_team_id: str | None,
        github_pat: str | None,
        github_repo: str | None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.linear_api_key = linear_api_key
        self.linear_team_id = linear_team_id
        self.github_pat = github_pat
        self.github_repo = github_repo
        self.timeout_seconds = timeout_seconds
        self._links: dict[UUID, dict] = {}  # incident → created refs

    # ---- Linear ----

    def _linear(self, query: str, variables: dict) -> dict:
        data = _post(
            "https://api.linear.app/graphql",
            {"query": query, "variables": variables},
            {"Authorization": self.linear_api_key or ""},
            self.timeout_seconds,
        )
        if data.get("errors"):
            raise RuntimeError(data["errors"][0].get("message", "Linear error"))
        return data.get("data", {})

    def create_linear_issue(self, incident: Incident, context: str) -> dict | None:
        """`issueCreate` → {identifier, url}. Skips when Linear isn't configured."""
        if not (self.linear_api_key and self.linear_team_id):
            return None
        title = f"[PocketSRE] {incident.severity.value} on {incident.service}: {incident.summary[:80]}"
        data = self._linear(
            "mutation($title:String!,$description:String!,$teamId:String!){"
            "issueCreate(input:{title:$title,description:$description,teamId:$teamId}){"
            "success issue{identifier url}}}",
            {
                "title": title,
                "description": f"Incident `{incident.id}` ({incident.source})\n\n{context}",
                "teamId": self.linear_team_id,
            },
        )
        result = data.get("issueCreate", {})
        if not result.get("success"):
            raise RuntimeError("Linear issueCreate returned success=false")
        return result["issue"]

    def update_linear_issue(self, issue_id_url: str, note: str) -> None:
        """Append a comment to a Linear issue (issueUpdate is complex; commentCreate is simpler)."""
        if not self.linear_api_key:
            return
        # commentCreate needs issueId; we store it in _links
        issue_id = next(
            (r.get("linear_id") for r in self._links.values() if r.get("linear_url") == issue_id_url),
            None,
        )
        if not issue_id:
            return
        self._linear(
            "mutation($issueId:String!,$body:String!){"
            "commentCreate(input:{issueId:$issueId,body:$body}){success}}",
            {"issueId": issue_id, "body": note},
        )

    # ---- GitHub ----

    def create_github_issue(self, incident: Incident, context: str) -> dict | None:
        """`POST /repos/{repo}/issues` → {number, html_url}. Skips when PAT/repo unset."""
        if not (self.github_pat and self.github_repo):
            return None
        title = f"[PocketSRE] {incident.severity.value} on {incident.service}: {incident.summary[:80]}"
        data = _post(
            f"https://api.github.com/repos/{self.github_repo}/issues",
            {
                "title": title,
                "body": f"Incident `{incident.id}` ({incident.source})\n\n{context}",
                "labels": ["pocketsre", "incident"],
            },
            {
                "Authorization": f"token {self.github_pat}",
                "Accept": "application/vnd.github+json",
            },
            self.timeout_seconds,
        )
        return {"number": data.get("number"), "html_url": data.get("html_url")}

    # ---- Orchestration ----

    def create_issue(self, incident: Incident, context: str, code_level: bool) -> dict:
        """Code-level → GitHub + Linear. Infra-only → Linear only."""
        refs: dict = {"incident_id": str(incident.id)}
        try:
            linear = self.create_linear_issue(incident, context)
            if linear:
                refs["linear_url"] = linear["url"]
                refs["linear_id"] = linear["identifier"]
        except (HTTPError, URLError, RuntimeError) as exc:
            refs["linear_error"] = str(exc)
        if code_level:
            try:
                gh = self.create_github_issue(incident, context)
                if gh:
                    refs["github_url"] = gh["html_url"]
                    refs["github_number"] = gh["number"]
            except (HTTPError, URLError) as exc:
                refs["github_error"] = str(exc)
        self._links[incident.id] = refs
        return refs

    def link_pr(self, incident: Incident, pr_url: str) -> None:
        """Record the Devin PR on both trackers."""
        refs = self._links.get(incident.id, {})
        if refs.get("linear_url"):
            try:
                self.update_linear_issue(refs["linear_url"], f"Fix PR opened by Devin: {pr_url}")
            except Exception:
                pass
        if refs.get("github_number") and self.github_pat:
            try:
                _post(
                    f"https://api.github.com/repos/{self.github_repo}/issues/{refs['github_number']}/comments",
                    {"body": f"Fix PR opened by Devin: {pr_url}"},
                    {
                        "Authorization": f"token {self.github_pat}",
                        "Accept": "application/vnd.github+json",
                    },
                    self.timeout_seconds,
                )
            except Exception:
                pass

    def pr_status(self, pr_url: str) -> dict | None:
        """`GET /repos/{repo}/pulls/{num}` — merged/open state for follow-up posts."""
        if not (self.github_pat and self.github_repo) or "/pull/" not in pr_url:
            return None
        num = pr_url.rsplit("/", 1)[-1]
        try:
            data = _get(
                f"https://api.github.com/repos/{self.github_repo}/pulls/{num}",
                {
                    "Authorization": f"token {self.github_pat}",
                    "Accept": "application/vnd.github+json",
                },
                self.timeout_seconds,
            )
            return {
                "state": data.get("state"),
                "merged": data.get("merged", False),
                "merged_by": (data.get("merged_by") or {}).get("login"),
            }
        except Exception:
            return None
