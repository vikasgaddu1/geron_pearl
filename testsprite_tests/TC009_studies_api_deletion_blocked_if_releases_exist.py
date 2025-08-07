import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_study_deletion_blocked_if_releases_exist():
    # Helper to create a study
    def create_study(label: str):
        payload = {"label": label}
        resp = requests.post(f"{BASE_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a study
    def delete_study(study_id: int):
        resp = requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Helper to create a database release for a study
    def create_database_release(study_id: int, label: str):
        payload = {"study_id": study_id, "label": label}
        resp = requests.post(f"{BASE_URL}/api/v1/database-releases", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["id"]

    # Helper to delete a database release
    def delete_database_release(database_release_id: int):
        resp = requests.delete(f"{BASE_URL}/api/v1/database-releases/{database_release_id}", headers=HEADERS, timeout=TIMEOUT)
        return resp

    study_label = f"test-study-{uuid.uuid4()}"
    release_label = f"test-release-{uuid.uuid4()}"

    study_id = None
    release_id = None

    try:
        # Create a new study
        study_id = create_study(study_label)

        # Attempt to delete study immediately - should succeed (200)
        resp = delete_study(study_id)
        assert resp.status_code == 200, f"Expected 200 on deleting study without releases, got {resp.status_code}"

        # Re-create the study for next test
        study_id = create_study(study_label + "-2")

        # Create a database release linked to the study
        release_id = create_database_release(study_id, release_label)

        # Attempt to delete study with dependent release - should be blocked with 400
        resp = delete_study(study_id)
        assert resp.status_code == 400, f"Expected 400 on deleting study with dependent releases, got {resp.status_code}"
        # Optionally check error message contains indication of dependent releases
        assert "dependent" in resp.text.lower() or "release" in resp.text.lower(), "Error message does not indicate dependent releases"

    finally:
        # Cleanup: delete database release if exists
        if release_id is not None:
            try:
                delete_database_release(release_id)
            except Exception:
                pass
        # Cleanup: delete study if exists
        if study_id is not None:
            try:
                delete_study(study_id)
            except Exception:
                pass


test_study_deletion_blocked_if_releases_exist()