import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def create_package(name: str):
    payload = {"name": name}
    resp = requests.post(f"{BASE_URL}/api/v1/packages", json=payload, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    assert "id" in data, f"Response JSON does not contain 'id': {data}"
    return data["id"]

def delete_package(package_id: int):
    resp = requests.delete(f"{BASE_URL}/api/v1/packages/{package_id}", headers=HEADERS, timeout=TIMEOUT)
    # Deletion may be blocked if items exist, ignore errors here for cleanup
    return resp

def create_text_element(label: str, type_: str):
    payload = {"label": label, "type": type_}
    resp = requests.post(f"{BASE_URL}/api/v1/text-elements", json=payload, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    assert "id" in data, f"Response JSON does not contain 'id': {data}"
    return data["id"]

def delete_text_element(text_element_id: int):
    resp = requests.delete(f"{BASE_URL}/api/v1/text-elements/{text_element_id}", headers=HEADERS, timeout=TIMEOUT)
    return resp

def create_package_item(package_id: int, item_payload: dict):
    resp = requests.post(f"{BASE_URL}/api/v1/packages/{package_id}/items", json=item_payload, headers=HEADERS, timeout=TIMEOUT)
    return resp

def delete_package_item(item_id: int):
    resp = requests.delete(f"{BASE_URL}/api/v1/packages/items/{item_id}", headers=HEADERS, timeout=TIMEOUT)
    return resp

def test_packages_api_create_polymorphic_package_item_composite_key_uniqueness():
    # Setup: create a package and required text elements (footnote and acronym) for references
    package_name = f"test-package-{uuid.uuid4()}"
    package_id = create_package(package_name)

    footnote_label = f"Footnote {uuid.uuid4()}"
    acronym_label = f"Acronym {uuid.uuid4()}"
    footnote_id = create_text_element(footnote_label, "footnote")
    acronym_id = create_text_element(acronym_label, "acronyms_set")

    try:
        # Define a polymorphic package item payload (TLF type example)
        item_payload = {
            "type": "tlf",
            "label": "Item 1",
            "tlf_details": {
                "population": "Safety",
                "analysis": "Analysis 1"
            },
            "footnotes": [footnote_id],
            "acronyms": [acronym_id]
        }

        # 1) Create first item - expect success 201
        resp1 = create_package_item(package_id, item_payload)
        assert resp1.status_code == 201, f"Expected 201 Created, got {resp1.status_code}"
        item1_id = resp1.json()["id"]

        # 2) Create duplicate item with same composite key - expect 400
        resp2 = create_package_item(package_id, item_payload)
        assert resp2.status_code == 400, f"Expected 400 for duplicate composite key, got {resp2.status_code}"

        # 3) Create item with missing references (footnotes/acronyms) - expect 400 or 404
        invalid_payload = {
            "type": "tlf",
            "label": "Item 2",
            "tlf_details": {
                "population": "Safety",
                "analysis": "Analysis 2"
            },
            "footnotes": [999999],  # Non-existent footnote id
            "acronyms": [acronym_id]
        }
        resp3 = create_package_item(package_id, invalid_payload)
        assert resp3.status_code in (400, 404), f"Expected 400 or 404 for missing footnote ref, got {resp3.status_code}"

        # 4) Create item with non-existent package_id - expect 404
        non_existent_package_id = 999999999
        resp4 = requests.post(
            f"{BASE_URL}/api/v1/packages/{non_existent_package_id}/items",
            json=item_payload,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        assert resp4.status_code == 404, f"Expected 404 for non-existent package, got {resp4.status_code}"

    finally:
        # Cleanup: delete created package items, text elements, and package
        try:
            if 'item1_id' in locals():
                delete_package_item(item1_id)
        except Exception:
            pass
        try:
            delete_text_element(footnote_id)
        except Exception:
            pass
        try:
            delete_text_element(acronym_id)
        except Exception:
            pass
        try:
            delete_package(package_id)
        except Exception:
            pass

test_packages_api_create_polymorphic_package_item_composite_key_uniqueness()