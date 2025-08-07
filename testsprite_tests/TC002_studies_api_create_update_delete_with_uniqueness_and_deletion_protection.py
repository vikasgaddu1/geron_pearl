import requests
import time
import websocket
import json

BASE_URL = "http://0.0.0.0:8000"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30


def test_studies_api_create_update_delete_with_uniqueness_and_deletion_protection():
    # Helper to create a study
    def create_study(label):
        payload = {"study_label": label}
        resp = requests.post(f"{BASE_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Helper to update a study
    def update_study(study_id, label):
        payload = {"study_label": label}
        resp = requests.put(f"{BASE_URL}/api/v1/studies/{study_id}", json=payload, headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Helper to delete a study
    def delete_study(study_id):
        resp = requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)
        return resp

    # Step 1: Create a new study with a unique label
    unique_label = f"test-study-{int(time.time()*1000)}"
    create_resp = create_study(unique_label)
    assert create_resp.status_code == 201, f"Expected 201 Created, got {create_resp.status_code}"
    study = create_resp.json()
    study_id = study.get("id")
    assert study_id is not None, "Created study response missing 'id'"

    try:
        # Step 2: Attempt to create another study with the same label (should fail with 400)
        dup_resp = create_study(unique_label)
        assert dup_resp.status_code == 400, f"Expected 400 for duplicate label, got {dup_resp.status_code}"
        dup_json = dup_resp.json()
        assert "already exists" in dup_json.get("detail", "").lower() or "duplicate" in dup_json.get("detail", "").lower()

        # Step 3: Update the existing study to a new unique label (should succeed)
        new_label = unique_label + "-updated"
        update_resp = update_study(study_id, new_label)
        assert update_resp.status_code == 200, f"Expected 200 OK on update, got {update_resp.status_code}"
        updated_study = update_resp.json()
        assert updated_study.get("study_label") == new_label

        # Step 4: Attempt to update the study to a label that duplicates another study (create second study first)
        second_label = f"second-study-{int(time.time()*1000)}"
        second_create_resp = create_study(second_label)
        assert second_create_resp.status_code == 201, f"Expected 201 Created for second study, got {second_create_resp.status_code}"
        second_study_id = second_create_resp.json().get("id")
        assert second_study_id is not None

        # Try to update second study to new_label which is already taken
        dup_update_resp = update_study(second_study_id, new_label)
        assert dup_update_resp.status_code == 400, f"Expected 400 for duplicate label on update, got {dup_update_resp.status_code}"
        dup_update_json = dup_update_resp.json()
        assert "already exists" in dup_update_json.get("detail", "").lower() or "duplicate" in dup_update_json.get("detail", "").lower()

        # Step 5: Attempt to delete the first study while it has no dependent database releases (should succeed)
        del_resp = delete_study(study_id)
        assert del_resp.status_code == 200, f"Expected 200 OK on delete, got {del_resp.status_code}"

        # Step 6: Create a study and a dependent database release to test deletion protection
        protected_label = f"protected-study-{int(time.time()*1000)}"
        protected_create_resp = create_study(protected_label)
        assert protected_create_resp.status_code == 201
        protected_study_id = protected_create_resp.json().get("id")
        assert protected_study_id is not None

        # Create a database release dependent on this study
        release_payload = {"database_release_label": "release1", "study_id": protected_study_id}
        release_resp = requests.post(f"{BASE_URL}/api/v1/database-releases", json=release_payload, headers=HEADERS, timeout=TIMEOUT)
        assert release_resp.status_code == 201, f"Expected 201 Created for database release, got {release_resp.status_code}"
        release_id = release_resp.json().get("id")
        assert release_id is not None

        # Attempt to delete the protected study (should fail with 400 due to dependent releases)
        del_protected_resp = delete_study(protected_study_id)
        assert del_protected_resp.status_code == 400, f"Expected 400 on delete with dependent releases, got {del_protected_resp.status_code}"
        del_protected_json = del_protected_resp.json()
        assert "dependent" in del_protected_json.get("detail", "").lower() or "release" in del_protected_json.get("detail", "").lower()

        # Cleanup: delete the database release, then delete the protected study
        del_release_resp = requests.delete(f"{BASE_URL}/api/v1/database-releases/{release_id}", headers=HEADERS, timeout=TIMEOUT)
        assert del_release_resp.status_code == 200, f"Expected 200 OK on release delete, got {del_release_resp.status_code}"

        del_protected_study_resp = delete_study(protected_study_id)
        assert del_protected_study_resp.status_code == 200, f"Expected 200 OK on protected study delete after release deletion, got {del_protected_study_resp.status_code}"

        # Cleanup: delete second study
        del_second_resp = delete_study(second_study_id)
        assert del_second_resp.status_code == 200, f"Expected 200 OK on second study delete, got {del_second_resp.status_code}"

    finally:
        # Cleanup in case of early failure
        try:
            requests.delete(f"{BASE_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)
        except Exception:
            pass


def test_websocket_subscribe_studies():
    ws_url = "ws://0.0.0.0:8000/api/v1/ws/studies"
    messages = []

    def on_message(ws, message):
        messages.append(message)

    def on_error(ws, error):
        raise Exception(f"WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        pass

    def on_open(ws):
        # No special message needed to subscribe, just open connection
        pass

    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    # Run websocket in a thread and wait briefly to receive initial snapshot
    import threading

    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    time.sleep(3)  # wait for initial snapshot

    ws.close()
    wst.join(timeout=1)

    # Validate that at least one message (initial snapshot) was received
    assert len(messages) > 0, "Expected at least one message from WebSocket initial snapshot"

    # Validate message format (JSON with expected keys)
    for msg in messages:
        data = json.loads(msg)
        assert isinstance(data, dict), "WebSocket message should be a JSON object"
        # Expect keys like 'studies' or 'event' in the snapshot or events
        assert any(k in data for k in ("studies", "event", "type")), "WebSocket message missing expected keys"


test_studies_api_create_update_delete_with_uniqueness_and_deletion_protection()
test_websocket_subscribe_studies()