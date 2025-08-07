import requests
import json
import time

BASE_URL = "http://0.0.0.0:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30


def test_database_releases_create_update_delete_with_study_scoping_and_deletion_protection():
    # Helper to create a study
    def create_study(study_label):
        resp = requests.post(
            f"{BASE_URL}/api/v1/studies",
            headers=HEADERS,
            json={"study_label": study_label},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 201, f"Failed to create study: {resp.text}"
        return resp.json()["id"]

    # Helper to delete a study
    def delete_study(study_id):
        resp = requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", timeout=TIMEOUT)
        # Deletion may be blocked if releases exist, so 400 is acceptable here
        assert resp.status_code in (200, 400, 404)

    # Helper to create a database release
    def create_database_release(label, study_id):
        resp = requests.post(
            f"{BASE_URL}/api/v1/database-releases",
            headers=HEADERS,
            json={"database_release_label": label, "study_id": study_id},
            timeout=TIMEOUT,
        )
        return resp

    # Helper to update a database release
    def update_database_release(database_release_id, label, study_id):
        resp = requests.put(
            f"{BASE_URL}/api/v1/database-releases/{database_release_id}",
            headers=HEADERS,
            json={"database_release_label": label, "study_id": study_id},
            timeout=TIMEOUT,
        )
        return resp

    # Helper to delete a database release
    def delete_database_release(database_release_id):
        resp = requests.delete(
            f"{BASE_URL}/api/v1/database-releases/{database_release_id}", timeout=TIMEOUT
        )
        return resp

    # Helper to create a reporting effort blocking deletion
    def create_reporting_effort(label, study_id, database_release_id):
        resp = requests.post(
            f"{BASE_URL}/api/v1/reporting-efforts",
            headers=HEADERS,
            json={
                "database_release_label": label,
                "study_id": study_id,
                "database_release_id": database_release_id,
            },
            timeout=TIMEOUT,
        )
        return resp

    # Create a study to scope releases
    study_label = f"test-study-for-db-release-{int(time.time()*1000)}"
    study_id = create_study(study_label)

    try:
        # Create a database release scoped to the study
        release_label = "release-1"
        resp = create_database_release(release_label, study_id)
        assert resp.status_code == 201, f"Create release failed: {resp.text}"
        release_id = resp.json()["id"]

        try:
            # Attempt to create another release with the same label in the same study (should fail)
            resp_dup = create_database_release(release_label, study_id)
            assert resp_dup.status_code == 400, "Duplicate label allowed for same study"

            # Create a release with same label but different study (should succeed)
            other_study_label = f"other-study-for-db-release-{int(time.time()*1000)}"
            other_study_id = create_study(other_study_label)
            try:
                resp_other = create_database_release(release_label, other_study_id)
                assert resp_other.status_code == 201, "Same label allowed in different study"
                other_release_id = resp_other.json()["id"]

                # Update the original release label to a new unique label (should succeed)
                new_label = "release-1-updated"
                resp_update = update_database_release(release_id, new_label, study_id)
                assert resp_update.status_code == 200, f"Update release failed: {resp_update.text}"

                # Create another release in the same study to test duplicate on update
                third_label = "release-3"
                resp_third = create_database_release(third_label, study_id)
                assert resp_third.status_code == 201
                third_release_id = resp_third.json()["id"]
                
                # Try to update the third release to have the same label as the first (should fail)
                resp_update_dup = update_database_release(
                    third_release_id, new_label, study_id
                )
                assert (
                    resp_update_dup.status_code == 400
                ), "Duplicate label allowed on update"

                # Create a reporting effort linked to the release to block deletion
                reporting_label = "report-effort-1"
                resp_report = create_reporting_effort(
                    reporting_label, study_id, release_id
                )
                assert (
                    resp_report.status_code == 201
                ), f"Create reporting effort failed: {resp_report.text}"
                reporting_effort_id = resp_report.json()["id"]

                # Attempt to delete the database release (should be blocked)
                resp_del_blocked = delete_database_release(release_id)
                assert (
                    resp_del_blocked.status_code == 400
                ), "Deletion not blocked despite dependent reporting efforts"

                # Delete the reporting effort to unblock deletion
                resp_del_report = requests.delete(
                    f"{BASE_URL}/api/v1/reporting-efforts/{reporting_effort_id}",
                    timeout=TIMEOUT,
                )
                assert resp_del_report.status_code == 200, "Failed to delete reporting effort"

                # Now delete the database release (should succeed)
                resp_del = delete_database_release(release_id)
                assert resp_del.status_code == 200, f"Delete release failed: {resp_del.text}"

                # Delete the third release
                resp_del_third = delete_database_release(third_release_id)
                assert resp_del_third.status_code == 200, f"Delete third release failed: {resp_del_third.text}"
                
                # Delete the other release and study
                resp_del_other = delete_database_release(other_release_id)
                assert resp_del_other.status_code == 200, f"Delete other release failed: {resp_del_other.text}"
            finally:
                delete_study(other_study_id)

        finally:
            # Cleanup: delete release if still exists
            requests.delete(
                f"{BASE_URL}/api/v1/database-releases/{release_id}", timeout=TIMEOUT
            )
    finally:
        # Cleanup: delete study
        delete_study(study_id)


test_database_releases_create_update_delete_with_study_scoping_and_deletion_protection()