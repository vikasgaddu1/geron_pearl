import requests
import websocket
import json
import threading
import time

BASE_URL = "http://localhost:8000"
STUDIES_ENDPOINT = f"{BASE_URL}/api/v1/studies"
WS_URL = "ws://localhost:8000/api/v1/ws/studies"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30

def test_create_study_with_uniqueness_and_websocket_broadcast():
    created_study_id = None
    ws_messages = []

    def on_message(ws, message):
        ws_messages.append(message)

    def on_error(ws, error):
        # For test purposes, just print error
        print("WebSocket error:", error)

    def on_close(ws, close_status_code, close_msg):
        pass

    def on_open(ws):
        # No action needed on open for this test
        pass

    # Connect to WebSocket in a separate thread to listen for broadcasts
    ws = websocket.WebSocketApp(
        WS_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws_thread = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 5, "ping_timeout": 2})
    ws_thread.daemon = True
    ws_thread.start()

    # Wait briefly to ensure WS connection is established
    time.sleep(1)

    try:
        # Step 1: Create a new study with a unique label
        study_payload = {"label": "Unique Study Label TC002"}
        response = requests.post(STUDIES_ENDPOINT, headers=HEADERS, json=study_payload, timeout=TIMEOUT)
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        created_study = response.json()
        assert "id" in created_study, "Response JSON missing 'id'"
        created_study_id = created_study["id"]
        assert created_study.get("label") == study_payload["label"], "Created study label mismatch"

        # Wait briefly to allow WebSocket broadcast to be received
        time.sleep(1)

        # Validate WebSocket broadcast contains the created study info
        # We expect at least one message containing the new study label
        broadcast_received = False
        for msg in ws_messages:
            try:
                data = json.loads(msg)
                # The broadcast should include the study label and id
                if isinstance(data, dict):
                    # Check if the broadcast is about the created study
                    # The exact broadcast format is not specified, so check for label and id presence
                    if data.get("label") == study_payload["label"] and data.get("id") == created_study_id:
                        broadcast_received = True
                        break
                    # Or if broadcast is a list of studies, check if created study is in list
                    if isinstance(data.get("studies"), list):
                        for study in data["studies"]:
                            if study.get("id") == created_study_id and study.get("label") == study_payload["label"]:
                                broadcast_received = True
                                break
            except Exception:
                continue
        assert broadcast_received, "WebSocket broadcast for created study not received"

        # Step 2: Attempt to create a duplicate study with the same label (case-insensitive)
        duplicate_payload = {"label": "unique study label tc002"}  # different case to test case-insensitivity
        dup_response = requests.post(STUDIES_ENDPOINT, headers=HEADERS, json=duplicate_payload, timeout=TIMEOUT)
        assert dup_response.status_code == 400, f"Expected 400 for duplicate label, got {dup_response.status_code}"

    finally:
        # Cleanup: delete the created study if it exists
        if created_study_id is not None:
            try:
                del_response = requests.delete(f"{STUDIES_ENDPOINT}/{created_study_id}", timeout=TIMEOUT)
                # Accept 200 OK or 404 Not Found if already deleted
                assert del_response.status_code in (200, 404), f"Unexpected delete status {del_response.status_code}"
            except Exception:
                pass
        # Close WebSocket connection
        ws.close()
        ws_thread.join(timeout=2)

test_create_study_with_uniqueness_and_websocket_broadcast()