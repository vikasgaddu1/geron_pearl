import json
import time
import threading
import requests
import websocket

BASE_API_URL = "http://0.0.0.0:8000"
WS_URL = "ws://0.0.0.0:8000/api/v1/ws/studies"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30


def test_websocket_endpoint_real_time_updates_and_initial_snapshot():
    # Helper functions for CRUD on studies
    def create_study(label):
        payload = {"study_label": label}
        resp = requests.post(f"{BASE_API_URL}/api/v1/studies", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def update_study(study_id, new_label):
        payload = {"study_label": new_label}
        resp = requests.put(f"{BASE_API_URL}/api/v1/studies/{study_id}", json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def delete_study(study_id):
        resp = requests.delete(f"{BASE_API_URL}/api/v1/studies/{study_id}", headers=HEADERS, timeout=TIMEOUT)
        # Deletion might be blocked if dependent releases exist, but for our test it should succeed
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        return resp

    # Storage for websocket messages
    ws_messages = []

    # WebSocket event handler
    def on_message(ws, message):
        try:
            data = json.loads(message)
            ws_messages.append(data)
        except Exception:
            pass

    def on_error(ws, error):
        ws_messages.append({"error": str(error)})

    def on_close(ws, close_status_code, close_msg):
        ws_messages.append({"closed": True, "code": close_status_code, "msg": close_msg})

    def on_open(ws):
        pass

    # Create a study to test create event broadcast
    study_label = f"ws_test_study_{int(time.time())}"
    study = create_study(study_label)
    study_id = study["id"]

    try:
        # Start websocket client in a thread
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

        # Wait for connection upgrade and initial snapshot
        timeout = time.time() + 10
        while time.time() < timeout:
            if ws.sock and ws.sock.connected:
                break
            time.sleep(0.1)
        else:
            ws.close()
            assert False, "WebSocket connection failed to upgrade"

        # Wait to receive initial snapshot message
        time.sleep(2)
        # Check initial snapshot presence: expect a message with type 'studies_update' containing studies list
        initial_snapshots = [m for m in ws_messages if isinstance(m, dict) and "type" in m and m["type"] == "studies_update"]
        assert initial_snapshots, "No initial snapshot message received on WebSocket"

        # Check that the created study is in the initial snapshot
        studies_list = initial_snapshots[-1].get("data", [])
        assert any(s.get("id") == study_id and s.get("study_label") == study_label for s in studies_list), "Created study not in initial snapshot"

        # Clear messages for next events
        ws_messages.clear()

        # Test create event broadcast: create another study
        new_study_label = f"ws_test_study_create_{int(time.time())}"
        new_study = create_study(new_study_label)
        new_study_id = new_study["id"]

        # Wait for create event broadcast
        timeout = time.time() + 10
        while time.time() < timeout:
            if any(m.get("type") == "study_created" and m.get("data", {}).get("id") == new_study_id for m in ws_messages):
                break
            time.sleep(0.1)
        else:
            assert False, "Create event not broadcasted via WebSocket"

        # Clear messages for update event
        ws_messages.clear()

        # Test update event broadcast: update the new study label
        updated_label = new_study_label + "_updated"
        updated_study = update_study(new_study_id, updated_label)

        # Wait for update event broadcast
        timeout = time.time() + 10
        while time.time() < timeout:
            if any(m.get("type") == "study_updated" and m.get("data", {}).get("id") == new_study_id and m.get("data", {}).get("study_label") == updated_label for m in ws_messages):
                break
            time.sleep(0.1)
        else:
            assert False, "Update event not broadcasted via WebSocket"

        # Clear messages for delete event
        ws_messages.clear()

        # Test delete event broadcast: delete the new study
        del_resp = delete_study(new_study_id)
        assert del_resp.status_code == 200, f"Failed to delete study {new_study_id}"

        # Wait for delete event broadcast
        timeout = time.time() + 10
        while time.time() < timeout:
            if any(m.get("type") == "study_deleted" and m.get("data", {}).get("id") == new_study_id for m in ws_messages):
                break
            time.sleep(0.1)
        else:
            assert False, "Delete event not broadcasted via WebSocket"

    finally:
        # Cleanup: delete the first created study
        delete_study(study_id)
        ws.close()
        ws_thread.join(timeout=5)


test_websocket_endpoint_real_time_updates_and_initial_snapshot()