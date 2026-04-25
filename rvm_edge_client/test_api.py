import requests

BACKEND_URL = "http://127.0.0.1:5000"

payload = {
    "qr_data": "dummy_user_123",
    "points_added": 15,
    "bottles_added": 3,
    "location": "Main Library Entrance",
    "machine_id": "RVM-MAIN-001",
    "description": "Recycled Bottles",
    "category": "Aluminum"
}

print(f"Sending dummy transaction to {BACKEND_URL}/api/add_points...")

try:
    response = requests.post(f"{BACKEND_URL}/api/add_points", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
