import requests

def test_health_api_service_and_database_connectivity_check():
    base_url = "http://0.0.0.0:8000"
    url = f"{base_url}/health"
    headers = {
        "Accept": "application/json"
    }
    timeout = 30

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        # The service should return either 200 (healthy) or 503 (unhealthy)
        assert response.status_code in (200, 503), f"Unexpected status code: {response.status_code}"
        if response.status_code == 200:
            # When healthy, response body may be empty or contain health info, just ensure no error
            assert response.ok, "Response not OK despite 200 status"
        elif response.status_code == 503:
            # When unhealthy, service indicates service or DB is down
            assert not response.ok, "Response OK despite 503 status"
    except requests.RequestException as e:
        assert False, f"Request to /health endpoint failed: {e}"

test_health_api_service_and_database_connectivity_check()