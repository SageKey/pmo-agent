"""FastAPI integration tests for /api/v1/initiatives."""

import pytest

API = "/api/v1/initiatives"


class TestListInitiatives:
    def test_returns_31_from_seed(self, api_client):
        r = api_client.get(f"{API}/")
        assert r.status_code == 200
        assert len(r.json()) == 31

    def test_filter_by_status(self, api_client):
        r = api_client.get(f"{API}/", params={"status": "Active"})
        assert r.status_code == 200
        for init in r.json():
            assert init["status"] == "Active"

    def test_filter_it_only(self, api_client):
        r = api_client.get(f"{API}/", params={"it_only": True})
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 19
        assert all(i["it_involvement"] for i in rows)

    def test_filter_non_it(self, api_client):
        r = api_client.get(f"{API}/", params={"it_only": False})
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 12
        assert not any(i["it_involvement"] for i in rows)

    def test_initiative_shape(self, api_client):
        rows = api_client.get(f"{API}/").json()
        for init in rows:
            for key in ("id", "name", "status", "it_involvement", "priority",
                        "project_count", "projects"):
                assert key in init, f"{init.get('id')} missing {key}"


class TestGetInitiative:
    def test_returns_detail_with_projects(self, api_client):
        r = api_client.get(f"{API}/INIT-01")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == "INIT-01"
        assert body["name"] == "Supply Chain Modernization"
        assert body["it_involvement"] is True
        assert body["project_count"] > 0
        assert isinstance(body["projects"], list)

    def test_unknown_404(self, api_client):
        r = api_client.get(f"{API}/NOT-REAL")
        assert r.status_code == 404


class TestCreateInitiative:
    def test_create_minimal(self, api_client):
        r = api_client.post(
            f"{API}/",
            json={"id": "TST-INIT", "name": "Test Initiative"},
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Test Initiative"
        assert r.json()["it_involvement"] is False

    def test_duplicate_409(self, api_client):
        api_client.post(f"{API}/", json={"id": "DUP-1", "name": "dup"})
        r = api_client.post(f"{API}/", json={"id": "DUP-1", "name": "dup2"})
        assert r.status_code == 409


class TestUpdateInitiative:
    def test_patch_fields(self, api_client):
        r = api_client.patch(
            f"{API}/INIT-01",
            json={"description": "Updated description", "it_involvement": True},
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated description"

    def test_unknown_404(self, api_client):
        r = api_client.patch(f"{API}/NOT-REAL", json={"name": "x"})
        assert r.status_code == 404


class TestDeleteInitiative:
    def test_delete_unlinks_projects(self, api_client):
        # Create initiative + project linked to it
        api_client.post(
            f"{API}/", json={"id": "DEL-INIT", "name": "To Delete", "it_involvement": True}
        )
        api_client.post(
            "/api/v1/portfolio/",
            json={"id": "DEL-PROJ", "name": "Linked", "initiative_id": "DEL-INIT"},
        )

        r = api_client.delete(f"{API}/DEL-INIT")
        assert r.status_code == 204

        # Initiative gone
        assert api_client.get(f"{API}/DEL-INIT").status_code == 404

        # Project still exists but initiative_id is NULL
        proj = api_client.get("/api/v1/portfolio/DEL-PROJ").json()
        assert proj["initiative_id"] is None
