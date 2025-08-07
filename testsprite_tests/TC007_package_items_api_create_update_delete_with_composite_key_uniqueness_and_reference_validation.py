import requests
import websocket
import json
import threading
import time

BASE_URL = "http://0.0.0.0:8000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def test_package_items_create_update_delete_composite_key_and_reference_validation():
    # Helper functions to create required resources: Study and Package
    def create_study(label):
        payload = {"study_label": label}
        r = requests.post(f"{BASE_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["id"]

    def delete_study(study_id):
        requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", timeout=TIMEOUT)

    def create_package(name):
        payload = {"package_name": name}
        r = requests.post(f"{BASE_URL}/api/v1/packages", json=payload, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["id"]

    def delete_package(package_id):
        requests.delete(f"{BASE_URL}/api/v1/packages/{package_id}", timeout=TIMEOUT)

    # Create Study and Package for testing
    study_id = None
    package_id = None
    item_id = None
    try:
        study_id = create_study("test-study-for-package-items")
        package_id = create_package("test-package-for-items")

        # 1) Test creating a package item with valid references and composite key uniqueness
        item_payload = {
            "package_id": package_id,
            "study_id": study_id,
            "item_type": "TLF",
            "item_subtype": "Table",
            "item_code": "TBL001"
        }
        # POST /api/v1/packages/{package_id}/items
        r = requests.post(f"{BASE_URL}/api/v1/packages/{package_id}/items", json=item_payload, headers=HEADERS, timeout=TIMEOUT)
        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"
        item = r.json()
        item_id = item["id"]
        assert item["study_id"] == study_id
        assert item["item_code"] == "TBL001"

        # 2) Test creating duplicate package item with same composite key (package_id + label + study_id)
        r_dup = requests.post(f"{BASE_URL}/api/v1/packages/{package_id}/items", json=item_payload, headers=HEADERS, timeout=TIMEOUT)
        assert r_dup.status_code == 400, f"Expected 400 for duplicate composite key, got {r_dup.status_code}"
        assert "already exists" in r_dup.text.lower() or "duplicate" in r_dup.text.lower()

        # 3) Test creating package item with missing references (e.g. invalid study_id)
        invalid_payload = item_payload.copy()
        invalid_payload["study_id"] = 999999999  # Non-existent study_id
        r_invalid = requests.post(f"{BASE_URL}/api/v1/packages/{package_id}/items", json=invalid_payload, headers=HEADERS, timeout=TIMEOUT)
        assert r_invalid.status_code in (400, 404), f"Expected 400 or 404 for missing study ref, got {r_invalid.status_code}"

        # 4) Test updating the package item (PUT /api/v1/packages/items/{item_id})
        update_payload = {
            "item_code": "TBL001-updated"
        }
        r_update = requests.put(f"{BASE_URL}/api/v1/packages/items/{item_id}", json=update_payload, headers=HEADERS, timeout=TIMEOUT)
        assert r_update.status_code == 200, f"Expected 200 OK on update, got {r_update.status_code}"
        updated_item = r_update.json()
        assert updated_item["item_code"] == "TBL001-updated"

        # 5) Test updating non-existent item returns 404
        r_update_404 = requests.put(f"{BASE_URL}/api/v1/packages/items/999999999", json=update_payload, headers=HEADERS, timeout=TIMEOUT)
        assert r_update_404.status_code == 404, f"Expected 404 for update non-existent item, got {r_update_404.status_code}"

        # 6) Test deleting the package item (DELETE /api/v1/packages/items/{item_id})
        r_delete = requests.delete(f"{BASE_URL}/api/v1/packages/items/{item_id}", timeout=TIMEOUT)
        assert r_delete.status_code == 200, f"Expected 200 OK on delete, got {r_delete.status_code}"

        # 7) Test deleting already deleted/non-existent item returns 404
        r_delete_404 = requests.delete(f"{BASE_URL}/api/v1/packages/items/{item_id}", timeout=TIMEOUT)
        assert r_delete_404.status_code == 404, f"Expected 404 for delete non-existent item, got {r_delete_404.status_code}"

    finally:
        # Cleanup created resources
        if item_id:
            try:
                requests.delete(f"{BASE_URL}/api/v1/packages/items/{item_id}", timeout=TIMEOUT)
            except Exception:
                pass
        if package_id:
            try:
                delete_package(package_id)
            except Exception:
                pass
        if study_id:
            try:
                delete_study(study_id)
            except Exception:
                pass

def test_websocket_subscribe_package_items():
    # Test WebSocket subscribe to /api/v1/ws/studies to confirm upgrade and initial snapshot
    ws_url = "ws://0.0.0.0:8000/api/v1/ws/studies"
    messages = []
    error = None

    def on_message(ws, message):
        messages.append(message)

    def on_error(ws, err):
        nonlocal error
        error = err

    def on_open(ws):
        # No special message needed, just subscribe
        pass

    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_open=on_open)

    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    time.sleep(3)  # Wait for connection and initial messages

    ws.close()
    wst.join(timeout=5)

    assert error is None, f"WebSocket error occurred: {error}"
    assert len(messages) > 0, "Expected at least one message from WebSocket initial snapshot"
    # Check that initial snapshot contains studies list or event type
    found_snapshot = any("studies" in msg.lower() or "snapshot" in msg.lower() for msg in messages)
    assert found_snapshot, "Initial snapshot message not found in WebSocket messages"

# Run the test function for TC007
test_package_items_create_update_delete_composite_key_and_reference_validation()