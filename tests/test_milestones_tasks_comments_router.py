"""FastAPI integration tests for /api/v1/milestones, /tasks, /comments."""

import pytest

M_API = "/api/v1/milestones"
T_API = "/api/v1/tasks"
C_API = "/api/v1/comments"
P_API = "/api/v1/portfolio"


@pytest.fixture
def project_id(api_client):
    """A real project ID from the seeded portfolio."""
    return api_client.get(f"{P_API}/").json()[0]["id"]


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------

class TestMilestonesRouter:
    def test_list_returns_array(self, api_client, project_id):
        r = api_client.get(f"{M_API}/{project_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_roundtrip(self, api_client, project_id):
        r = api_client.post(
            f"{M_API}/{project_id}",
            json={"title": "Ship MVP", "due_date": "2026-06-01"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["title"] == "Ship MVP"
        assert body["due_date"] == "2026-06-01"

        # Now in the list
        titles = [m["title"] for m in api_client.get(f"{M_API}/{project_id}").json()]
        assert "Ship MVP" in titles

    def test_update_milestone(self, api_client, project_id):
        created = api_client.post(
            f"{M_API}/{project_id}",
            json={"title": "Original"},
        ).json()
        mid = created["id"]

        r = api_client.put(
            f"{M_API}/id/{mid}",
            json={
                "project_id": project_id,
                "title": "Renamed",
                "status": "in_progress",
                "progress_pct": 0.5,
            },
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Renamed"
        assert r.json()["status"] == "in_progress"

    def test_complete_milestone(self, api_client, project_id):
        created = api_client.post(
            f"{M_API}/{project_id}", json={"title": "To Complete"}
        ).json()
        r = api_client.post(f"{M_API}/id/{created['id']}/complete")
        assert r.status_code == 204

    def test_delete_milestone(self, api_client, project_id):
        created = api_client.post(
            f"{M_API}/{project_id}", json={"title": "To Delete"}
        ).json()
        r = api_client.delete(f"{M_API}/id/{created['id']}")
        assert r.status_code == 204


# ---------------------------------------------------------------------------
# Tasks (read-only for now)
# ---------------------------------------------------------------------------

class TestTasksRouter:
    def test_list_tasks_returns_array(self, api_client, project_id):
        r = api_client.get(f"{T_API}/{project_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class TestCommentsRouter:
    def test_list_comments(self, api_client, project_id):
        r = api_client.get(f"{C_API}/{project_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_comment(self, api_client, project_id):
        r = api_client.post(
            f"{C_API}/{project_id}",
            json={"author": "Brett", "body": "Looks good"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["author"] == "Brett"
        assert body["body"] == "Looks good"

        comments = api_client.get(f"{C_API}/{project_id}").json()
        assert any(c["body"] == "Looks good" for c in comments)

    def test_delete_comment(self, api_client, project_id):
        created = api_client.post(
            f"{C_API}/{project_id}",
            json={"author": "x", "body": "ephemeral"},
        ).json()
        r = api_client.delete(f"{C_API}/id/{created['id']}")
        assert r.status_code == 204
