# RVM Edge Client Integration Guide

This guide outlines how the `rvm_edge_client` communicates with the Eco-Points Flask Backend.

## Overview
The edge client simulates a Reverse Vending Machine (RVM) and interacts with the backend over HTTP. The backend controller (`rpi_controller.py`) exposes three primary endpoints under the `/api/rpi` prefix to handle machine operations.

### Base URL
`http://<YOUR_BACKEND_IP>:<PORT>` (e.g., `http://127.0.0.1:5000`)

---

## 1. Start a Session
Initiated when a user scans their QR code at the machine.

- **Endpoint**: `POST /api/rpi/session/start`
- **Request Body**:
  ```json
  {
    "user_qr": "USER-123",       // The display_id embedded in the QR code
    "machine_uuid": "RVM-001"    // Unique identifier of the machine
  }
  ```
- **Success Response** (`201 Created`):
  ```json
  {
    "success": true,
    "account": { "name": "John Doe" },
    "session": { "session_id": 12, "status": "active" }
  }
  ```

---

## 2. Deposit an Item
Triggered each time the machine accepts and verifies a recyclable item.

- **Endpoint**: `POST /api/rpi/item/deposit`
- **Request Body**:
  ```json
  {
    "session_id": 12,
    "item_type": "PET Plastic",
    "points": 10,
    "weight_grams": 50,
    "brand": "Unknown",
    "condition": "Good",
    "size_category": "Medium"
  }
  ```
- **Success Response** (`201 Created`):
  ```json
  {
    "success": true,
    "item": { "id": 45, "pointsAwarded": 10, "status": "Accepted" }
  }
  ```

---

## 3. End Session (Finalize)
Called when the user finishes depositing items. Commits the session and credits points to the user's wallet.

- **Endpoint**: `POST /api/rpi/session/end`
- **Request Body**:
  ```json
  {
    "session_id": 12,
    "machine_uuid": "RVM-001"
  }
  ```
- **Success Response** (`200 OK`):
  ```json
  {
    "success": true,
    "session": {
      "id": 12,
      "status": "completed",
      "itemCount": 5,
      "totalPointsEarned": 50
    }
  }
  ```

## Environment Setup
In your `rvm_edge_client` directory, ensure your `.env` file matches your backend server configuration:
```env
BACKEND_URL=http://127.0.0.1:5000
MACHINE_ID=RVM-MAIN-001
LOCATION=Institute of Technology
```
