import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30

def test_text_elements_api_duplicate_prevention_case_insensitive():
    # Prepare two labels that differ only by case and spaces
    label_original = "Duplicate Test Label"
    label_duplicate_variation = "  duplicate  test LABEL  "
    text_element_type = "title"  # Using one of the allowed enum types

    created_id = None

    try:
        # Step 1: Create a new text element with label_original
        payload_create = {
            "label": label_original,
            "type": text_element_type
        }
        response_create = requests.post(
            f"{BASE_URL}/api/v1/text-elements",
            json=payload_create,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        assert response_create.status_code == 201, f"Expected 201 Created, got {response_create.status_code}"
        created_id = response_create.json().get("id")
        assert created_id is not None, "Created text element ID not returned"

        # Step 2: Attempt to create a duplicate text element with label_duplicate_variation (case- and space-insensitive)
        payload_duplicate_create = {
            "label": label_duplicate_variation,
            "type": text_element_type
        }
        response_dup_create = requests.post(
            f"{BASE_URL}/api/v1/text-elements",
            json=payload_duplicate_create,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        assert response_dup_create.status_code == 400, (
            f"Expected 400 Bad Request on duplicate create, got {response_dup_create.status_code}"
        )

        # Step 3: Attempt to update the existing text element to a duplicate label variation (should fail)
        # First create a second distinct text element to update
        payload_second = {
            "label": "Another Unique Label",
            "type": text_element_type
        }
        response_second = requests.post(
            f"{BASE_URL}/api/v1/text-elements",
            json=payload_second,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        assert response_second.status_code == 201, f"Expected 201 Created for second element, got {response_second.status_code}"
        second_id = response_second.json().get("id")
        assert second_id is not None, "Second text element ID not returned"

        # Attempt to update second element's label to the duplicate variation
        payload_update_dup = {
            "label": label_duplicate_variation,
            "type": text_element_type
        }
        response_update_dup = requests.put(
            f"{BASE_URL}/api/v1/text-elements/{second_id}",
            json=payload_update_dup,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        assert response_update_dup.status_code == 400, (
            f"Expected 400 Bad Request on duplicate update, got {response_update_dup.status_code}"
        )

    finally:
        # Cleanup: delete created text elements if they exist
        if created_id is not None:
            requests.delete(f"{BASE_URL}/api/v1/text-elements/{created_id}", headers=HEADERS, timeout=TIMEOUT)
        if 'second_id' in locals() and second_id is not None:
            requests.delete(f"{BASE_URL}/api/v1/text-elements/{second_id}", headers=HEADERS, timeout=TIMEOUT)

test_text_elements_api_duplicate_prevention_case_insensitive()