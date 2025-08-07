import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def test_text_elements_api_search_by_label_with_filtering_and_pagination():
    # Create multiple text elements with distinct labels and types for testing search, filtering, and pagination
    created_ids = []
    try:
        # Prepare test data
        test_elements = [
            {"label": "Alpha Label", "type": "title"},
            {"label": "Beta Label", "type": "footnote"},
            {"label": "Gamma Label", "type": "title"},
            {"label": "Delta Label", "type": "population_set"},
            {"label": "Epsilon Label", "type": "title"},
            {"label": "Zeta Label", "type": "footnote"},
        ]

        # Create text elements
        for elem in test_elements:
            payload = {
                "label": elem["label"],
                "type": elem["type"]
            }
            resp = requests.post(
                f"{BASE_URL}/api/v1/text-elements",
                json=payload,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            assert resp.status_code == 201, f"Failed to create text element: {resp.text}"
            data = resp.json()
            assert "id" in data, "Response missing 'id'"
            created_ids.append(data["id"])

        # Test search by label substring "Label" (should return all)
        params = {"q": "Label"}
        resp = requests.get(
            f"{BASE_URL}/api/v1/text-elements/search",
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Search request failed: {resp.text}"
        results = resp.json()
        assert isinstance(results, list), "Search results should be a list"
        assert len(results) >= len(test_elements), "Search results count less than created elements"
        # Check that all returned items contain "Label" in label (case-insensitive)
        for item in results:
            assert "label" in item, "Result item missing 'label'"
            assert isinstance(item["label"], str), "label must be a string"
            assert "label" in item["label"].lower(), f"Label '{item['label']}' does not contain 'label'"
    finally:
        # Cleanup: delete created elements
        for elem_id in created_ids:
            requests.delete(
                f"{BASE_URL}/api/v1/text-elements/{elem_id}",
                headers=HEADERS,
                timeout=TIMEOUT,
            )

test_text_elements_api_search_by_label_with_filtering_and_pagination()
