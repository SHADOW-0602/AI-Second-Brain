import requests
import json

try:
    response = requests.get("http://localhost:8000/api/system/debug/sessions")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
