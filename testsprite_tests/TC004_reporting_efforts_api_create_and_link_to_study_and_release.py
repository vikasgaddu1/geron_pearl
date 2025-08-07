import requests
import uuid

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30

def test_reporting_efforts_create_and_link_to_study_and_release():
    study_id = None
    database_release_id = None
    reporting_effort_id = None

    # Helper to create a study
    def create_study():
        label = f"Test Study {uuid.uuid4()}"
        payload = {"label": label}
        resp = requests.post(f"{BASE_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a study
    def delete_study(sid):
        requests.delete(f"{BASE_URL}/api/v1/studies/{sid}", headers=HEADERS, timeout=TIMEOUT)

    # Helper to create a database release linked to a study
    def create_database_release(sid):
        label = f"Release {uuid.uuid4()}"
        payload = {"label": label, "study_id": sid}
        resp = requests.post(f"{BASE_URL}/api/v1/database-releases", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a database release
    def delete_database_release(drid):
        requests.delete(f"{BASE_URL}/api/v1/database-releases/{drid}", headers=HEADERS, timeout=TIMEOUT)

    # Helper to create a reporting effort
    def create_reporting_effort(sid, drid):
        label = f"Reporting Effort {uuid.uuid4()}"
        payload = {
            "label": label,
            "study_id": sid,
            "database_release_id": drid
        }
        return requests.post(f"{BASE_URL}/api/v1/reporting-efforts", json=payload, headers=HEADERS, timeout=TIMEOUT)

    # Setup: create study and database release
    try:
        study_id = create_study()
        database_release_id = create_database_release(study_id)

        # 1) Successful creation linked to valid study and release
        resp = create_reporting_effort(study_id, database_release_id)
        assert resp.status_code == 201, f"Expected 201 Created, got {resp.status_code}"
        reporting_effort_id = resp.json().get("id")
        assert reporting_effort_id is not None, "Response missing reporting effort id"

        # 2) Foreign key mismatch (e.g. study_id and database_release_id do not belong together)
        # Create another study and try to link reporting effort with mismatched release
        other_study_id = create_study()
        try:
            payload = {
                "label": f"Mismatch Effort {uuid.uuid4()}",
                "study_id": other_study_id,
                "database_release_id": database_release_id  # release belongs to first study
            }
            resp_fk_mismatch = requests.post(f"{BASE_URL}/api/v1/reporting-efforts", json=payload, headers=HEADERS, timeout=TIMEOUT)
            assert resp_fk_mismatch.status_code == 400, f"Expected 400 for foreign key mismatch, got {resp_fk_mismatch.status_code}"
        finally:
            delete_study(other_study_id)

        # 3) Missing references: non-existent study_id
        payload_missing_study = {
            "label": f"Missing Study {uuid.uuid4()}",
            "study_id": 9999999999,  # presumably non-existent
            "database_release_id": database_release_id
        }
        resp_missing_study = requests.post(f"{BASE_URL}/api/v1/reporting-efforts", json=payload_missing_study, headers=HEADERS, timeout=TIMEOUT)
        assert resp_missing_study.status_code == 404, f"Expected 404 for missing study, got {resp_missing_study.status_code}"

        # 4) Missing references: non-existent database_release_id
        payload_missing_release = {
            "label": f"Missing Release {uuid.uuid4()}",
            "study_id": study_id,
            "database_release_id": 9999999999  # presumably non-existent
        }
        resp_missing_release = requests.post(f"{BASE_URL}/api/v1/reporting-efforts", json=payload_missing_release, headers=HEADERS, timeout=TIMEOUT)
        assert resp_missing_release.status_code == 404, f"Expected 404 for missing database release, got {resp_missing_release.status_code}"

    finally:
        # Cleanup reporting effort if created
        if reporting_effort_id:
            requests.delete(f"{BASE_URL}/api/v1/reporting-efforts/{reporting_effort_id}", headers=HEADERS, timeout=TIMEOUT)
        # Cleanup database release
        if database_release_id:
            delete_database_release(database_release_id)
        # Cleanup study
        if study_id:
            delete_study(study_id)

test_reporting_efforts_create_and_link_to_study_and_release()