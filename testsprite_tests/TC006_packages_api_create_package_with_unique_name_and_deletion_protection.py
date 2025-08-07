import requests
import uuid

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30


def test_packages_api_create_unique_name_and_deletion_protection():
    package_name = f"test-package-{uuid.uuid4()}"
    package_payload = {"name": package_name}

    # Create a new package with a unique name
    response_create = requests.post(
        f"{BASE_URL}/api/v1/packages",
        json=package_payload,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    assert response_create.status_code == 201, f"Expected 201, got {response_create.status_code}"
    package = response_create.json()
    package_id = package.get("id")
    assert package_id is not None, "Created package ID is missing"

    # Attempt to create another package with the same name (should fail with 400)
    response_duplicate = requests.post(
        f"{BASE_URL}/api/v1/packages",
        json=package_payload,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    assert response_duplicate.status_code == 400, f"Expected 400 on duplicate, got {response_duplicate.status_code}"

    # Attempt to delete the package (should succeed because no dependent items yet)
    response_delete_no_items = requests.delete(
        f"{BASE_URL}/api/v1/packages/{package_id}",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    assert response_delete_no_items.status_code == 200, f"Expected 200 on delete, got {response_delete_no_items.status_code}"


if __name__ == "__main__":
    test_packages_api_create_unique_name_and_deletion_protection()