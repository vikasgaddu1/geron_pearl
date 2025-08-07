import json
import threading
import time
import websocket
import requests

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/ws/studies"
HEADERS = {"Content-Type": "application/json"}
REQUEST_TIMEOUT = 30


def test_websocket_real_time_updates_and_initial_snapshot():
    # Storage for received websocket messages
    received_messages = []

    def on_message(ws, message):
        try:
            data = json.loads(message)
            received_messages.append(data)
        except Exception:
            # Ignore malformed messages
            pass

    def on_error(ws, error):
        # Append error info to messages for assertion
        received_messages.append({"error": str(error)})

    def on_close(ws, close_status_code, close_msg):
        received_messages.append({"closed": True, "code": close_status_code, "msg": close_msg})

    def on_open(ws):
        # No special action needed on open
        pass

    # Create a new study to trigger websocket broadcast
    study_payload = {
        "label": "ws_test_study_unique_label_12345",
        "description": "Test study for websocket real-time updates"
    }

    study_id = None
    ws = None

    try:
        # Connect to websocket in a separate thread
        ws = websocket.WebSocketApp(
            WS_URL,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 10, "ping_timeout": 5})
        ws_thread.daemon = True
        ws_thread.start()

        # Wait briefly for websocket connection to establish and receive initial snapshot
        timeout = time.time() + 10
        while not received_messages and time.time() < timeout:
            time.sleep(0.1)

        # Assert initial snapshot received (at least one message)
        assert len(received_messages) > 0, "No initial snapshot message received from websocket"

        # Create study via REST API to trigger broadcast
        resp = requests.post(
            f"{BASE_URL}/api/v1/studies",
            headers=HEADERS,
            json=study_payload,
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code == 201, f"Failed to create study, status code: {resp.status_code}"
        study_data = resp.json()
        study_id = study_data.get("id")
        assert study_id is not None, "Created study response missing 'id'"

        # Wait for websocket to receive broadcast of new study creation
        timeout = time.time() + 10
        while True:
            # Check if any received message contains the created study id and action create
            found = False
            for msg in received_messages:
                if (
                    isinstance(msg, dict)
                    and msg.get("action") in ("create", "refresh", "update")
                    and isinstance(msg.get("data"), dict)
                    and msg["data"].get("id") == study_id
                ):
                    found = True
                    break
            if found or time.time() > timeout:
                break
            time.sleep(0.1)

        assert found, "Did not receive websocket broadcast for study creation"

        # Update the study to trigger update broadcast
        update_payload = {
            "label": study_payload["label"],
            "description": "Updated description for websocket test"
        }
        resp = requests.put(
            f"{BASE_URL}/api/v1/studies/{study_id}",
            headers=HEADERS,
            json=update_payload,
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code == 200, f"Failed to update study, status code: {resp.status_code}"

        # Wait for websocket to receive broadcast of study update
        timeout = time.time() + 10
        found_update = False
        while True:
            for msg in received_messages:
                if (
                    isinstance(msg, dict)
                    and msg.get("action") == "update"
                    and isinstance(msg.get("data"), dict)
                    and msg["data"].get("id") == study_id
                    and msg["data"].get("description") == update_payload["description"]
                ):
                    found_update = True
                    break
            if found_update or time.time() > timeout:
                break
            time.sleep(0.1)

        assert found_update, "Did not receive websocket broadcast for study update"

        # Delete the study to trigger delete broadcast
        resp = requests.delete(
            f"{BASE_URL}/api/v1/studies/{study_id}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code == 200, f"Failed to delete study, status code: {resp.status_code}"

        # Wait for websocket to receive broadcast of study deletion
        timeout = time.time() + 10
        found_delete = False
        while True:
            for msg in received_messages:
                if (
                    isinstance(msg, dict)
                    and msg.get("action") == "delete"
                    and isinstance(msg.get("data"), dict)
                    and msg["data"].get("id") == study_id
                ):
                    found_delete = True
                    break
            if found_delete or time.time() > timeout:
                break
            time.sleep(0.1)

        assert found_delete, "Did not receive websocket broadcast for study deletion"

    finally:
        # Cleanup: ensure study is deleted if still exists
        if study_id is not None:
            try:
                requests.delete(
                    f"{BASE_URL}/api/v1/studies/{study_id}",
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
            except Exception:
                pass
        if ws:
            ws.close()


test_websocket_real_time_updates_and_initial_snapshot()