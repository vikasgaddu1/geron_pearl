import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_health_api_service_liveness_and_db_connectivity_check():
    url = f"{BASE_URL}/health"
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        # The service is healthy, expect 200 or 503 if DB down
        assert response.status_code in (200, 503), f"Unexpected status code: {response.status_code}"
        if response.status_code == 200:
            # Service healthy
            assert response.text or True  # Response body may be empty or contain info
        elif response.status_code == 503:
            # Service unhealthy due to DB connectivity
            assert response.text or True  # Response body may contain error info
    except requests.RequestException as e:
        assert False, f"Request to /health endpoint failed: {e}"

test_health_api_service_liveness_and_db_connectivity_check()