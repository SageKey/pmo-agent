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
# Tasks
# ---------------------------------------------------------------------------

class TestTasksRouter:
    def test_list_tasks_returns_array(self, api_client, project_id):
        r = api_client.get(f"{T_API}/{project_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_task(self, api_client, project_id):
        r = api_client.post(
            f"{T_API}/{project_id}",
            json={
                "title": "Design review",
                "assignee": "Marcus Bell",
                "priority": "High",
                "status": "not_started",
                "est_hours": 8,
                "start_date": "2026-05-01",
                "end_date": "2026-05-15",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["title"] == "Design review"
        assert body["assignee"] == "Marcus Bell"
        assert body["priority"] == "High"
        assert body["est_hours"] == 8.0

        # It should now appear in the list
        tasks = api_client.get(f"{T_API}/{project_id}").json()
        assert any(t["title"] == "Design review" for t in tasks)

    def test_create_task_under_milestone(self, api_client, project_id):
        ms = api_client.post(
            f"{M_API}/{project_id}", json={"title": "Discovery Phase"}
        ).json()
        r = api_client.post(
            f"{T_API}/{project_id}",
            json={"title": "Stakeholder interviews", "milestone_id": ms["id"]},
        )
        assert r.status_code == 201
        assert r.json()["milestone_id"] == ms["id"]

    def test_update_task(self, api_client, project_id):
        created = api_client.post(
            f"{T_API}/{project_id}", json={"title": "Original"}
        ).json()
        r = api_client.patch(
            f"{T_API}/id/{created['id']}",
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

    def test_complete_task(self, api_client, project_id):
        created = api_client.post(
            f"{T_API}/{project_id}", json={"title": "To complete"}
        ).json()
        r = api_client.post(f"{T_API}/id/{created['id']}/complete")
        assert r.status_code == 204

        tasks = api_client.get(f"{T_API}/{project_id}").json()
        match = next(t for t in tasks if t["id"] == created["id"])
        assert match["status"] == "complete"

    def test_delete_task(self, api_client, project_id):
        created = api_client.post(
            f"{T_API}/{project_id}", json={"title": "To delete"}
        ).json()
        r = api_client.delete(f"{T_API}/id/{created['id']}")
        assert r.status_code == 204

        tasks = api_client.get(f"{T_API}/{project_id}").json()
        assert not any(t["id"] == created["id"] for t in tasks)

    def test_update_nonexistent_404(self, api_client, project_id):
        r = api_client.patch(
            f"{T_API}/id/99999",
            json={"project_id": project_id, "title": "x"},
        )
        assert r.status_code == 404

    def test_delete_nonexistent_404(self, api_client):
        r = api_client.delete(f"{T_API}/id/99999")
        assert r.status_code == 404

    def test_task_notes_field(self, api_client, project_id):
        """v7 rename: description → notes. Rich HTML stored in notes column."""
        r = api_client.post(
            f"{T_API}/{project_id}",
            json={
                "title": "Task with notes",
                "notes": "<p>Some <strong>rich</strong> text</p>",
            },
        )
        assert r.status_code == 201
        assert r.json()["notes"] == "<p>Some <strong>rich</strong> text</p>"

    def test_task_updated_by_on_create(self, api_client, project_id):
        """updated_by captured on POST."""
        r = api_client.post(
            f"{T_API}/{project_id}",
            json={"title": "By test", "updated_by": "Marcus Bell"},
        )
        assert r.status_code == 201
        assert r.json()["updated_by"] == "Marcus Bell"

    def test_task_updated_by_on_update(self, api_client, project_id):
        """updated_by captured on PATCH — should reflect the latest editor."""
        created = api_client.post(
            f"{T_API}/{project_id}",
            json={"title": "Initial", "updated_by": "Alice"},
        ).json()
        assert created["updated_by"] == "Alice"

        r = api_client.patch(
            f"{T_API}/id/{created['id']}",
            json={
                "project_id": project_id,
                "title": "Renamed",
                "updated_by": "Bob",
            },
        )
        assert r.status_code == 200
        assert r.json()["updated_by"] == "Bob"


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
