# RVM Edge Client Integration Guide

This guide outlines how the `rvm_edge_client` communicates with the Eco-Points Flask Backend and the React Kiosk UI.

## HTTP Backend Overview
The edge client simulates a Reverse Vending Machine (RVM) and interacts with the backend over HTTP. The backend controller (`rpi_controller.py`) exposes three primary endpoints under the `/api/rpi` prefix to handle machine operations.

### Base URL
`http://<YOUR_BACKEND_IP>:<PORT>` (e.g., `http://127.0.0.1:5000`)

---

## 1. Authenticate QR Code
Initiated when a user scans their QR code at the machine. The backend validates the payload and returns the user's wallet ID and role.

- **Endpoint**: `POST /api/rpi/authenticate`
- **Headers**: `X-API-Key: <your_api_key_here>`
- **Request Body**:
  ```json
  {
    "qrPayload": "USER-123",
    "machineUuid": "RVM-001"
  }
  ```
- **Success Response** (`200 OK` or `201 Created`):
  ```json
  {
    "walletId": 12,
    "user": {
      "name": "John Doe",
      "role": "user"
    }
  }
  ```

---

## 2. Start a Session
Called immediately after successful authentication to initiate a transaction session for the user.

- **Endpoint**: `POST /api/rpi/session/start`
- **Headers**: `X-API-Key: <your_api_key_here>`
- **Request Body**:
  ```json
  {
    "walletId": 12,
    "machineUuid": "RVM-001"
  }
  ```
- **Success Response** (`200 OK` or `201 Created`):
  ```json
  {
    "session": { "id": 45, "status": "active" }
  }
  ```

---

## 3. Deposit an Item
Triggered each time the machine accepts and verifies a recyclable item.

- **Endpoint**: `POST /api/rpi/session/<session_id>/deposit`
- **Headers**: `X-API-Key: <your_api_key_here>`
- **Request Body**:
  ```json
  {
    "machineUuid": "RVM-001",
    "detectedClass": "Le Minerale",
    "confidenceScore": 0.95,
    "pointsAwarded": 10,
    "status": "Accepted"
  }
  ```
- **Success Response** (`200 OK` or `201 Created`):
  ```json
  {
    "success": true
  }
  ```

---

## 4. End Session (Finalize)
Called when the user finishes depositing items. Commits the session and updates the machine status.

- **Endpoint**: `POST /api/rpi/session/<session_id>/end`
- **Headers**: `X-API-Key: <your_api_key_here>`
- **Request Body**:
  ```json
  {
    "status": "completed",
    "machineUuid": "RVM-001"
  }
  ```
- **Success Response** (`200 OK` or `201 Created`):
  ```json
  {
    "success": true
  }
  ```

---

## WebSocket Kiosk UI Bridge
The python daemon (`main.py`) hosts a WebSocket server at `ws://localhost:8765` to drive the React Native (web) Kiosk interface.

### A. Python Daemon to React UI (Broadcasts)
* **`GO_IDLE`**: Transitions UI to Idle Screen (waiting for user).
* **`WAKE`**: Transitions UI to QR Scan Screen.
* **`LOGIN_SUCCESS`**: Transitions UI to Ready Screen. Payload: `{"userName": "name"}`.
* **`ADMIN_LOGIN`**: Transitions UI to Admin/Maintenance menu. Payload: `{"userName": "name"}`.
* **`LOGIN_DENIED`**: Transitions UI to Denied Screen (invalid QR).
* **`SET_DOOR_OPEN`**: Transitions UI to Door Open Screen.
* **`DOOR_CLOSED`**: Transitions UI back to Verifying Screen.
* **`BOTTLE_INSERTED`**: Transitions UI to Verifying/Processing Screen.
* **`VERIFY_SUCCESS`**: Transitions UI to Accepted Screen. Payload: `{"points": 10, "bottleCount": 1}`.
* **`VERIFY_FAIL`**: Transitions UI to Rejected Screen. Payload: `{"reason": "detail"}`.
* **`ADVANCE_THANK_YOU`**: Transitions UI to Thank You Screen.
* **`SET_BIN_FULL`**: Transitions UI to Bin Full Screen.
* **`SYSTEM_CLEAR`**: Resets UI state machine to Start Screen.

### B. React UI to Python Daemon (Control inputs)
* **`{"action": "WAKE"}`**: Sent when user taps Idle screen to wake up the system.
* **`{"action": "QR_SCANNED", "qr_data": "<token>"}`**: Sent when the React camera scans the QR code.
* **`{"action": "CANCEL"}`**: Sent when the user cancels scanning.
* **`{"action": "REPEAT_READY"}`**: Sent when user taps "Transact again" / "Try Again".
* **`{"action": "FINISH"}`**: Sent when user taps "Finish" / "End Transaction".

---

## Environment Setup
In your `rvm_edge_client` directory, ensure your `.env` file matches your backend server configuration:
```env
BACKEND_URL=http://127.0.0.1:5000
MACHINE_ID=RVM-MAIN-001
LOCATION=Institute of Technology
CLI_MODE=false
API_KEY=your_api_key_here
QR_HMAC_SECRET=your_qr_hmac_secret_here
```

