"""FastAPI integration tests for /api/v1/assignments, /financials, /timesheets, /snapshots, /jira."""

import pytest

A_API = "/api/v1/assignments"
F_API = "/api/v1/financials"
T_API = "/api/v1/timesheets"
S_API = "/api/v1/snapshots"
J_API = "/api/v1/jira"
P_API = "/api/v1/portfolio"
R_API = "/api/v1/roster"


@pytest.fixture
def project_id(api_client):
    return api_client.get(f"{P_API}/").json()[0]["id"]


@pytest.fixture
def person_name(api_client):
    return api_client.get(f"{R_API}/").json()[0]["name"]


# ===========================================================================
# Assignments
# ===========================================================================

class TestAssignmentsRouter:
    def test_list_all(self, api_client):
        r = api_client.get(f"{A_API}/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_filter_by_project(self, api_client, project_id):
        r = api_client.get(f"{A_API}/", params={"project_id": project_id})
        assert r.status_code == 200
        for a in r.json():
            assert a["project_id"] == project_id

    def test_upsert_assignment(self, api_client, project_id, person_name):
        payload = {
            "project_id": project_id,
            "person_name": person_name,
            "role_key": "ba",
            "allocation_pct": 0.5,
        }
        r = api_client.post(f"{A_API}/", json=payload)
        assert r.status_code == 201, r.text
        assert r.json()["allocation_pct"] == 0.5

    def test_alloc_out_of_range_rejected(self, api_client, project_id, person_name):
        r = api_client.post(
            f"{A_API}/",
            json={
                "project_id": project_id,
                "person_name": person_name,
                "role_key": "ba",
                "allocation_pct": 1.5,  # > 1.0
            },
        )
        assert r.status_code == 400

    def test_delete_assignment(self, api_client, project_id, person_name):
        api_client.post(
            f"{A_API}/",
            json={
                "project_id": project_id,
                "person_name": person_name,
                "role_key": "pm",
                "allocation_pct": 0.25,
            },
        )
        r = api_client.delete(
            f"{A_API}/",
            params={
                "project_id": project_id,
                "person_name": person_name,
                "role_key": "pm",
            },
        )
        assert r.status_code == 204


# ===========================================================================
# Financials
# ===========================================================================

class TestFinancialsRouter:
    def test_list_vendors(self, api_client):
        r = api_client.get(f"{F_API}/vendors")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_invoices(self, api_client):
        r = api_client.get(f"{F_API}/invoices")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_monthly_requires_year(self, api_client):
        r = api_client.get(f"{F_API}/monthly")
        assert r.status_code == 422  # year is required

    def test_monthly_with_year(self, api_client):
        r = api_client.get(f"{F_API}/monthly", params={"year": 2026})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_costs_by_project(self, api_client):
        r = api_client.get(f"{F_API}/by-project")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_invoice_autocomputes_total(self, api_client):
        r = api_client.post(
            f"{F_API}/invoices",
            json={
                "month": "2026-04",
                "msa_amount": 10000,
                "tm_amount": 5000,
                "invoice_number": "INV-TEST-001",
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["total_amount"] == 15000

    def test_upsert_vendor(self, api_client):
        r = api_client.post(
            f"{F_API}/vendors",
            json={
                "name": "Test Consultant",
                "billing_type": "T&M",
                "hourly_rate": 150,
                "role_key": "developer",
            },
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Test Consultant"


# ===========================================================================
# Timesheets
# ===========================================================================

class TestTimesheetsRouter:
    def test_list_entries(self, api_client):
        r = api_client.get(f"{T_API}/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_with_filters(self, api_client):
        r = api_client.get(f"{T_API}/", params={"month": "2026-04"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_summary(self, api_client):
        r = api_client.get(f"{T_API}/summary")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_entry(self, api_client):
        # First create a vendor so consultant_id exists
        vendor = api_client.post(
            f"{F_API}/vendors",
            json={
                "name": "TS Vendor",
                "billing_type": "T&M",
                "hourly_rate": 100,
            },
        ).json()

        r = api_client.post(
            f"{T_API}/",
            json={
                "consultant_id": vendor["id"],
                "entry_date": "2026-04-01",
                "hours": 8.0,
                "work_type": "Project",
                "project_name": "Test",
            },
        )
        assert r.status_code == 201


# ===========================================================================
# Snapshots
# ===========================================================================

class TestSnapshotsRouter:
    def test_list_empty_initially(self, api_client, tmp_path, monkeypatch):
        # Point SnapshotStore at an isolated temp db
        from backend.app.config import settings as app_settings
        monkeypatch.setattr(
            app_settings, "snapshot_db_path", str(tmp_path / "snap.db")
        )
        r = api_client.get(f"{S_API}/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_latest_returns_null_when_empty(self, api_client, tmp_path, monkeypatch):
        from backend.app.config import settings as app_settings
        monkeypatch.setattr(
            app_settings, "snapshot_db_path", str(tmp_path / "snap2.db")
        )
        r = api_client.get(f"{S_API}/latest")
        assert r.status_code == 200

    def test_create_snapshot(self, api_client, tmp_path, monkeypatch):
        from backend.app.config import settings as app_settings
        monkeypatch.setattr(
            app_settings, "snapshot_db_path", str(tmp_path / "snap3.db")
        )
        r = api_client.post(f"{S_API}/", json={"notes": "test snapshot"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert "id" in body
        assert body["project_count"] > 0


# ===========================================================================
# Jira
# ===========================================================================

class TestJiraRouter:
    def test_sync_without_token_503(self, api_client, monkeypatch):
        """Without JIRA_API_TOKEN configured, sync must return 503 with a
        clear message — not crash the server."""
        # Ensure no token is visible
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        from backend.app.config import settings as app_settings
        monkeypatch.setattr(app_settings, "jira_api_token", None)

        r = api_client.post(f"{J_API}/sync")
        assert r.status_code == 503
        assert "JIRA_API_TOKEN" in r.json()["detail"]
