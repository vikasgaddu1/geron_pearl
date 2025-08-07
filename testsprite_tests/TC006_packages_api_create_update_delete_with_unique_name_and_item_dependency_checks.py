import requests
import time

BASE_URL = "http://0.0.0.0:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30


def test_packages_api_create_update_delete_unique_name_and_item_dependency_checks():
    package_url = f"{BASE_URL}/api/v1/packages"

    # Helper to create a package with a given name
    def create_package(name):
        payload = {"package_name": name}
        resp = requests.post(package_url, json=payload, headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Helper to delete a package by id
    def delete_package(package_id):
        resp = requests.delete(f"{package_url}/{package_id}", headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Step 1: Create a new package with a unique name
    unique_name = f"test-package-{int(time.time()*1000)}"
    resp_create = create_package(unique_name)
    assert resp_create.status_code == 201, f"Expected 201 Created, got {resp_create.status_code}"
    package = resp_create.json()
    package_id = package.get("id")
    assert package_id is not None, "Created package response missing 'id'"

    try:
        # Step 2: Attempt to create another package with the same name (should fail)
        resp_dup_create = create_package(unique_name)
        assert resp_dup_create.status_code == 400, f"Expected 400 for duplicate name, got {resp_dup_create.status_code}"
        assert "already exists" in resp_dup_create.text.lower() or "duplicate" in resp_dup_create.text.lower()

        # Step 3: Update the package with a new unique name
        new_unique_name = f"{unique_name}-updated"
        resp_update = requests.put(
            f"{package_url}/{package_id}",
            json={"package_name": new_unique_name},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        assert resp_update.status_code == 200, f"Expected 200 Updated, got {resp_update.status_code}"
        updated_package = resp_update.json()
        assert updated_package.get("package_name") == new_unique_name, "Package name not updated correctly"

        # Step 4: Attempt to update the package to a name that already exists (create another package first)
        resp_create_2 = create_package(f"{unique_name}-other")
        assert resp_create_2.status_code == 201, "Failed to create second package for update duplicate test"
        package2_id = resp_create_2.json().get("id")
        assert package2_id is not None

        try:
            resp_update_dup = requests.put(
                f"{package_url}/{package2_id}",
                json={"package_name": new_unique_name},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            assert resp_update_dup.status_code == 400, f"Expected 400 for duplicate name on update, got {resp_update_dup.status_code}"
            assert "already exists" in resp_update_dup.text.lower() or "duplicate" in resp_update_dup.text.lower()
        finally:
            # Clean up second package
            del_resp2 = delete_package(package2_id)
            assert del_resp2.status_code == 200, f"Failed to delete second package, got {del_resp2.status_code}"

        # Step 5: Attempt to delete the package while it has dependent items (simulate by creating an item)
        # First create a study for the package item
        study_payload = {"study_label": f"test-study-{int(time.time()*1000)}"}
        study_resp = requests.post(f"{BASE_URL}/api/v1/studies", json=study_payload, headers=HEADERS, timeout=TIMEOUT)
        assert study_resp.status_code == 201, f"Failed to create study, got {study_resp.status_code}"
        study_id = study_resp.json().get("id")
        
        # Create a package item to block deletion
        items_url = f"{package_url}/{package_id}/items"
        # Corrected item payload to include required fields according to expected schema
        item_payload = {
            "package_id": package_id,
            "study_id": study_id,
            "item_type": "TLF",
            "item_subtype": "Table",
            "item_code": f"TBL{int(time.time()*1000)}"
        }
        # Create the package item
        resp_create_item = requests.post(items_url, json=item_payload, headers=HEADERS, timeout=TIMEOUT)
        assert resp_create_item.status_code == 201, f"Expected 201 Created for package item, got {resp_create_item.status_code}"
        item_id = resp_create_item.json().get("id")
        assert item_id is not None

        try:
            # Now attempt to delete the package - should be blocked with 400 and error about dependent items
            resp_delete_blocked = delete_package(package_id)
            assert resp_delete_blocked.status_code == 400, f"Expected 400 blocked delete due to dependent items, got {resp_delete_blocked.status_code}"
            assert "dependent" in resp_delete_blocked.text.lower() or "items" in resp_delete_blocked.text.lower()
        finally:
            # Clean up the created item to allow package deletion
            resp_delete_item = requests.delete(f"{BASE_URL}/api/v1/packages/items/{item_id}", headers=HEADERS, timeout=TIMEOUT)
            assert resp_delete_item.status_code == 200, f"Failed to delete package item, got {resp_delete_item.status_code}"
            # Delete the study
            requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)

        # Step 6: Now delete the package successfully (no dependent items)
        resp_delete = delete_package(package_id)
        assert resp_delete.status_code == 200, f"Expected 200 Deleted, got {resp_delete.status_code}"

        # Step 7: Confirm package is deleted (GET should 404)
        resp_get_deleted = requests.get(f"{package_url}/{package_id}", headers=HEADERS, timeout=TIMEOUT)
        assert resp_get_deleted.status_code == 404, f"Expected 404 for deleted package, got {resp_get_deleted.status_code}"

    except Exception:
        # Attempt cleanup if test fails before deletion
        try:
            delete_package(package_id)
        except Exception:
            pass
        raise


test_packages_api_create_update_delete_unique_name_and_item_dependency_checks()
