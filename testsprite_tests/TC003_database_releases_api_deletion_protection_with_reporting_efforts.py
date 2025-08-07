import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_database_release_deletion_protection_with_reporting_efforts():
    # Helper to create a study
    def create_study():
        study_label = f"Test Study {uuid.uuid4()}"
        payload = {"label": study_label}
        resp = requests.post(f"{BASE_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a study
    def delete_study(study_id):
        requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)

    # Helper to create a database release
    def create_database_release(study_id):
        release_label = f"Release {uuid.uuid4()}"
        payload = {"label": release_label, "study_id": study_id}
        resp = requests.post(f"{BASE_URL}/api/v1/database-releases", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a database release
    def delete_database_release(database_release_id):
        requests.delete(f"{BASE_URL}/api/v1/database-releases/{database_release_id}", headers=HEADERS, timeout=TIMEOUT)

    # Helper to create a reporting effort
    def create_reporting_effort(study_id, database_release_id):
        effort_label = f"Effort {uuid.uuid4()}"
        payload = {
            "label": effort_label,
            "study_id": study_id,
            "database_release_id": database_release_id
        }
        resp = requests.post(f"{BASE_URL}/api/v1/reporting-efforts", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a reporting effort
    def delete_reporting_effort(reporting_effort_id):
        requests.delete(f"{BASE_URL}/api/v1/reporting-efforts/{reporting_effort_id}", headers=HEADERS, timeout=TIMEOUT)

    study_id = None
    database_release_id = None
    reporting_effort_id = None

    try:
        # Create a study
        study_id = create_study()

        # Create a database release linked to the study
        database_release_id = create_database_release(study_id)

        # Attempt to delete the database release without reporting efforts - should succeed with 200
        resp = requests.delete(f"{BASE_URL}/api/v1/database-releases/{database_release_id}", headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200 on delete without reporting efforts, got {resp.status_code}"

        # Re-create the database release for next test
        database_release_id = create_database_release(study_id)

        # Create a reporting effort linked to the study and database release
        reporting_effort_id = create_reporting_effort(study_id, database_release_id)

        # Attempt to delete the database release with dependent reporting efforts - should be blocked with 400
        resp = requests.delete(f"{BASE_URL}/api/v1/database-releases/{database_release_id}", headers=HEADERS, timeout=TIMEOUT)
        assert resp.status_code == 400, f"Expected 400 on delete with dependent reporting efforts, got {resp.status_code}"
        # Optionally check error message contains indication of dependent reporting efforts
        assert "dependent reporting efforts" in resp.text.lower() or "has dependent reporting efforts" in resp.text.lower()

    finally:
        # Cleanup: delete reporting effort if exists
        if reporting_effort_id:
            try:
                delete_reporting_effort(reporting_effort_id)
            except Exception:
                pass
        # Cleanup: delete database release if exists
        if database_release_id:
            try:
                delete_database_release(database_release_id)
            except Exception:
                pass
        # Cleanup: delete study if exists
        if study_id:
            try:
                delete_study(study_id)
            except Exception:
                pass


test_database_release_deletion_protection_with_reporting_efforts()