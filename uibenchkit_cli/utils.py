import requests

def verify_response(response):
    """Verify that a response is successful (200). Raises RequestException on failure."""
    if response.status_code != 200:
        try:
            data = response.json()
            message = data.get("message") or data.get("error") or "No message provided"
        except Exception:
            message = response.text or "No message provided"
        raise requests.RequestException(f"API request failed with status code {response.status_code}: {message}")
    return True
