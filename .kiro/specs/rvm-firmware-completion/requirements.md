# Requirements Document

## Introduction

The EcoPoints RVM edge client (`main.py` firmware daemon and `ui/` kiosk UI) is partially implemented. This document captures the 12 completion gaps as formal requirements, derived from the approved design document. All requirements target production correctness on Raspberry Pi hardware. No architectural changes are introduced.

---

## Glossary

- **Firmware**: `main.py` Python daemon running on the Raspberry Pi.
- **UI**: Expo Web kiosk application in `rvm_edge_client/ui/`.
- **UIBridge**: WebSocket server at `ws://localhost:8765` hosted by the Firmware.
- **HeartbeatThread**: Background daemon thread in the Firmware that periodically contacts the Backend.
- **Backend**: Flask HTTP API at the configured `BACKEND_URL`, prefixed `/api/rpi/`.
- **HardwareInterface**: Python class in `main.py` managing GPIO, camera, and YOLO.
- **KioskContext**: React context/reducer in `ui/src/context/KioskContext.tsx` that owns UI state.
- **useKioskTimer**: React hook in `ui/src/hooks/useKioskTimer.ts` that fires timed screen transitions.
- **useGPIOBridge**: React hook in `ui/src/hooks/useGPIOBridge.ts` that manages the WebSocket connection.
- **sendGPIOEvent**: Exported function from `useGPIOBridge.ts` that sends a JSON message over the WebSocket.
- **QRScanScreen**: UI screen component in `ui/src/screens/QRScanScreen.tsx` that handles QR HID input.
- **AdminNotesScreen**: UI screen component in `ui/src/screens/AdminNotesScreen.tsx` for admin log entry.
- **kioskApi**: Module `ui/src/api/kioskApi.ts` containing mock and utility API functions.
- **DEV_MODE**: Boolean constant derived from `EXPO_PUBLIC_DEV_MODE` env var; `true` on dev machine, `false` on device.
- **MACHINE_ID**: String env var identifying this RVM unit.
- **PIN_MOTOR_PULSE**: BCM 12 GPIO output pin sending step pulses to the stepper motor driver.
- **PIN_MOTOR_DIR**: BCM 16 GPIO output pin setting stepper motor direction.
- **PIN_MOTOR_ENABLE**: BCM 17 GPIO output pin enabling the stepper motor driver (active-LOW — LOW = enabled).
- **PIN_MOTOR_HOME**: BCM 6 GPIO input pin connected to the homing sensor (SW2) that detects when the motor reaches the home position.
- **PIN_IN_PROGRESS**: BCM 26 GPIO output pin driving the In Progress indicator light (active-LOW — LOW = ON).
- **PIN_STROBE**: BCM 22 GPIO output pin driving the strobe light.
- **POINTS_DEFAULT**: Hardcoded fallback points lookup dict in `main.py`.
- **YOLO**: YOLOv11 object detection model loaded from `models/best.pt`.

---

## Requirements

### Requirement 1: Periodic Heartbeat

**User Story:** As a system operator, I want the RVM to periodically report its online status and bin capacity, so that the backend can accurately track machine availability.

#### Acceptance Criteria

1. WHEN Firmware startup completes (after `boot_sequence()` returns), THE HeartbeatThread SHALL start and send `POST /api/rpi/machine/heartbeat` to the Backend repeatedly, with a 30-second interval starting after each request completes or times out.
2. WHEN a heartbeat POST is sent, THE HeartbeatThread SHALL include `machineUuid` (string value of `MACHINE_ID`) and `isCapacityFull` (boolean, current bin-full state from `hw.is_bin_full()`) in the JSON request body.
3. WHEN a heartbeat POST request fails for any reason (network error, non-2xx response, or timeout), THE HeartbeatThread SHALL emit a warning-level log entry indicating the failure reason, then resume the next 30-second interval without raising an exception or crashing.
4. THE HeartbeatThread SHALL enforce an HTTP request timeout of 10 seconds per POST call; a request that exceeds 10 seconds SHALL be treated as a failure per criterion 3.
5. THE HeartbeatThread SHALL run as a daemon thread so that it does not block Firmware process shutdown.

---

### Requirement 2: Bin-Full Machine Status Sync

**User Story:** As a system operator, I want the RVM to notify the backend whenever the bin transitions between full and clear states, so that the backend reflects real-time bin capacity.

#### Acceptance Criteria

1. WHEN the bin sensor reading transitions from clear to full (50 consecutive HIGH reads confirmed), THE HardwareInterface SHALL POST `{"machineUuid": MACHINE_ID, "isCapacityFull": true}` to `POST /api/rpi/machine/status` with a 10-second timeout.
2. WHEN the bin sensor reading transitions from clear to full, THE HardwareInterface SHALL broadcast `SET_BIN_FULL` to all connected UI clients.
3. WHEN the bin sensor reading transitions from full to clear (5 consecutive LOW reads confirmed), THE HardwareInterface SHALL POST `{"machineUuid": MACHINE_ID, "isCapacityFull": false}` to `POST /api/rpi/machine/status` with a 10-second timeout.
4. WHEN the bin sensor reading transitions from full to clear, THE HardwareInterface SHALL broadcast `CLEAR_BIN_FULL` to all connected UI clients.
5. THE HardwareInterface SHALL only call `POST /api/rpi/machine/status` on state-change edge transitions (False→True or True→False), not on every sensor poll tick.
6. THE status sync HTTP POST SHALL be executed without blocking the bin-monitor poll loop (e.g. in a background thread or fire-and-forget).
7. WHEN the `POST /api/rpi/machine/status` call fails (non-2xx, timeout, or network error), THE HardwareInterface SHALL log the failure and SHALL NOT retry automatically.

---

### Requirement 3: Points Configuration Fetch

**User Story:** As a system operator, I want the RVM to load the points table from the backend at startup, so that point awards reflect the latest organization configuration.

#### Acceptance Criteria

1. WHEN Firmware startup completes (after `boot_sequence()` returns), THE Firmware SHALL call `GET /api/rpi/config/points/<org_id>` — where `org_id` is the `organizationId` returned by the preceding `POST /api/rpi/machine/identify` call — to fetch the active points configuration, with a 10-second timeout.
2. WHEN the points config fetch returns HTTP 200 and a `config` dict is present in the response body, THE Firmware SHALL use the returned config dict for all `pointsAwarded` calculations for the duration of that run.
3. IF the points config fetch fails (non-200 response, timeout, or network error), THEN THE Firmware SHALL log a warning and use `POINTS_DEFAULT` for all `pointsAwarded` calculations.
4. `POINTS_DEFAULT` SHALL contain a non-zero integer mapping for every size token that `verify_bottle()` can return, including: `extra small`, `xs`, `small`, `s`, `medium`, `m`, `large`, `l`, `1000ml`, `750ml`, `551ml`, `600ml`, `550ml`, `500ml`, `351ml`, `350ml`, `330ml`, `290ml`, `289ml`, `250ml`, `125ml`.

---

### Requirement 4: Session Timeout

**User Story:** As a system operator, I want idle transaction sessions to expire automatically, so that the machine does not remain locked to an inactive user indefinitely.

#### Acceptance Criteria

1. WHEN the Firmware is waiting for a `REPEAT_READY` or `FINISH` action during a transaction, THE Firmware SHALL enforce a 300-second inactivity timeout measured using a monotonic clock.
2. IF no user action (`REPEAT_READY` or `FINISH`) is received within 300 seconds, THEN THE Firmware SHALL call `POST /api/rpi/session/<session_id>/end` with `{"status": "timed_out", "machineUuid": MACHINE_ID}`.
3. WHEN a session times out, THE Firmware SHALL broadcast `ADVANCE_THANK_YOU` to the UI and set `transacting = False` to exit the transaction loop.
4. WHEN a `REPEAT_READY` or `FINISH` action is received before the 300-second timeout elapses, THE Firmware SHALL process the action and cancel the remaining timeout countdown.
5. THE `wait_for_action` function SHALL return within `timeout_seconds + 1.0` wall-clock seconds under all execution paths, including network delay and poll-interval overhead.
6. WHEN `POST /api/rpi/session/<session_id>/end` fails during a timeout path (network error or non-2xx), THE Firmware SHALL log the failure and continue to broadcast `ADVANCE_THANK_YOU` and reset state.

---

### Requirement 5: Stepper Motor GPIO Control

**User Story:** As a hardware engineer, I want the stepper motor to be driven by real GPIO output using PULSE/DIR/ENABLE signals, so that the sorting actuator moves the bottle into the camera viewport correctly on physical hardware.

#### Acceptance Criteria

1. THE Firmware SHALL define the following motor pin constants:
   - `PIN_MOTOR_PULSE = 12` (BCM 12) — step pulse output
   - `PIN_MOTOR_DIR = 16` (BCM 16) — direction output
   - `PIN_MOTOR_ENABLE = 17` (BCM 17) — driver enable output, active-LOW (LOW = enabled, HIGH = disabled)
   - `PIN_MOTOR_HOME = 6` (BCM 6) — homing sensor input (SW2)
   - `PIN_IN_PROGRESS = 26` (BCM 26) — In Progress indicator output, active-LOW (LOW = ON)
   - `PIN_STROBE = 22` (BCM 22) — strobe light output
2. WHEN `_setup_gpio()` runs on hardware with GPIO available, THE HardwareInterface SHALL configure all motor pins as outputs with safe initial states: `PIN_MOTOR_ENABLE` HIGH (disabled), `PIN_MOTOR_PULSE` LOW, `PIN_MOTOR_DIR` LOW, `PIN_IN_PROGRESS` HIGH (off), `PIN_STROBE` LOW (off); and `PIN_MOTOR_HOME` as input with pull-up.
3. WHEN `spin_motor(steps)` is called with GPIO available, THE HardwareInterface SHALL: assert `PIN_MOTOR_ENABLE` LOW (enable driver), turn on `PIN_IN_PROGRESS` LOW and `PIN_STROBE` HIGH, send `steps` PULSE signals on `PIN_MOTOR_PULSE` (each pulse: HIGH for 0.5 ms, LOW for 0.5 ms), then assert `PIN_MOTOR_ENABLE` HIGH (disable driver) and turn off indicator/strobe.
4. WHEN `spin_motor(steps)` is called and `PIN_MOTOR_HOME` reads LOW before the pulse sequence completes, THE HardwareInterface SHALL stop pulsing immediately (homing position reached) and log the event.
5. IF GPIO is unavailable, THEN `spin_motor(steps)` SHALL simulate by sleeping for `steps * 0.001` seconds without asserting any GPIO pin.
6. WHEN `_setup_gpio()` completes, `PIN_MOTOR_ENABLE` SHALL be HIGH (driver disabled) and `PIN_IN_PROGRESS` SHALL be HIGH (indicator off).
7. WHEN `shutdown_gpio()` completes, `PIN_MOTOR_ENABLE` SHALL be HIGH (driver disabled), `PIN_IN_PROGRESS` SHALL be HIGH (off), and `PIN_STROBE` SHALL be LOW (off).

---

### Requirement 6: YOLO Confidence Score Passthrough

**User Story:** As a data analyst, I want deposit records to contain the actual YOLO detection confidence, so that recycling transaction data reflects true model certainty.

#### Acceptance Criteria

1. WHEN `verify_bottle()` identifies a valid bottle with confidence score in `[0.0, 1.0]`, THE HardwareInterface SHALL return a 4-tuple `(True, brand_name: str, size_category: str, confidence_score: float)`.
2. IF `verify_bottle()` finds no detections meeting the configured detection threshold (default 0.55), THEN THE HardwareInterface SHALL return `(False, "None", "None", 0.0)`.
3. IF `verify_bottle()` fails due to camera unavailability or missing YOLO model, THEN THE HardwareInterface SHALL return `(False, "None", "None", 0.0)`.
4. WHEN the Firmware submits a deposit to `POST /api/rpi/session/<session_id>/deposit`, THE Firmware SHALL set `confidenceScore` to the `confidence_score` value returned by `verify_bottle()`, rounded to 4 decimal places using half-up rounding.
5. THE Firmware SHALL NOT use any hardcoded literal value for `confidenceScore` in the deposit payload.
6. THE detection confidence threshold SHALL be a configurable parameter (default 0.55) within the valid range `[0.01, 1.0]`; values outside this range SHALL be rejected at startup with a descriptive error.

---

### Requirement 7: QR Scan WebSocket Wiring

**User Story:** As a kiosk user, I want QR scans to be sent to the firmware in production mode, so that authentication is processed by the backend rather than a local mock.

#### Acceptance Criteria

1. IF `DEV_MODE` is `false` and `QRScanScreen` receives a scan result that has not already been processed, THEN THE QRScanScreen SHALL call `sendGPIOEvent({ action: "QR_SCANNED", qr_data: <scanned_data> })` and enter a loading state until a firmware response event is received.
2. WHEN `DEV_MODE` is `true` and `QRScanScreen` receives a scan result, THE QRScanScreen SHALL call `loginWithQR(data)` from `kioskApi`; IF the result is `{ success: true, role: "user" }` THEN dispatch `LOGIN_SUCCESS`; IF the role is an admin role THEN dispatch `ADMIN_LOGIN`; IF `success` is `false` THEN dispatch `LOGIN_DENIED`.
3. THE QRScanScreen SHALL NOT call `sendGPIOEvent` in the `DEV_MODE` branch, and SHALL NOT call `loginWithQR` in the production (`DEV_MODE=false`) branch.

---

### Requirement 8: FINISH Event Timer Guard

**User Story:** As a kiosk user, I want the session to end correctly when the acceptance timer expires, so that the firmware receives the FINISH signal on physical hardware regardless of development mode.

#### Acceptance Criteria

1. WHEN the `ACCEPTED` screen timer fires (after 8 000 ms) or the `REJECTED` screen timer fires (after 15 000 ms), THE `useKioskTimer` SHALL call `sendGPIOEvent({ action: "FINISH" })` unconditionally — not gated on `DEV_MODE` being `false`.
2. WHEN the `ACCEPTED` or `REJECTED` screen timer fires, THE `useKioskTimer` SHALL call `sendGPIOEvent({ action: "FINISH" })` before calling `dispatch(action)`.
3. WHEN the `ACCEPTED` or `REJECTED` screen timer fires and the WebSocket is not open (e.g. `sendGPIOEvent` silently no-ops), THE `useKioskTimer` SHALL still call `dispatch(action)` so the UI screen advances locally.

---

### Requirement 9: SYSTEM_CLEAR vs GO_IDLE Event Semantics

**User Story:** As a UI developer, I want the firmware to use distinct events for idle entry and session reset, so that the kiosk UI transitions to the correct screen in each case.

#### Acceptance Criteria

1. WHEN the Firmware enters the idle wait loop (before polling for a `WAKE` event at the top of the main loop), THE Firmware SHALL broadcast `GO_IDLE` to the UI.
2. WHEN a session ends with status `completed`, THE Firmware SHALL broadcast `SYSTEM_CLEAR` to reset the UI to the Start Screen.
3. IF a session ends due to a 300-second inactivity timeout, THEN THE Firmware SHALL broadcast `ADVANCE_THANK_YOU` followed by `SYSTEM_CLEAR` after approximately 60 seconds to reset the UI to the Start Screen.
4. WHEN the UI receives a `GO_IDLE` event and the current screen is not in `SYSTEM_SCREENS` (i.e. not `DOOR_OPEN`), THE KioskContext reducer SHALL transition `screen` to `IDLE` and clear session transaction data.
5. WHEN the UI receives a `SYSTEM_CLEAR` event, THE KioskContext reducer SHALL transition `screen` to `START` and preserve the `isBinFull` flag.

---

### Requirement 10: Dead Code Removal

**User Story:** As a developer, I want unused files and mock functions removed from the codebase, so that the production build contains only active, tested code.

#### Acceptance Criteria

1. THE `BinFullScreen.tsx` file SHALL be deleted from `ui/src/screens/`, and no file in the `ui/` directory tree SHALL contain an import of `BinFullScreen`.
2. THE `App.tsx` router SHALL NOT import or render `BinFullScreen` in any code path.
3. THE `kioskApi` module SHALL NOT export `getVerificationResult` or `getSystemStatus`; any call sites that previously imported these functions SHALL be removed.
4. THE `kioskApi.loginWithQR` function SHALL remain in the module with a comment of the form `// DEV_MODE only — not called in production (DEV_MODE=false)` immediately above the function declaration.

---

### Requirement 11: Admin Log Routing via WebSocket

**User Story:** As an admin user, I want machine log submissions to route through the firmware, so that the correct backend endpoint and authentication header are used.

#### Acceptance Criteria

1. WHEN `AdminNotesScreen` submits a log entry, THE AdminNotesScreen SHALL call `sendGPIOEvent({ action: "SUBMIT_LOG", payload: { actionType, status, notes } })` and SHALL NOT make any direct HTTP call to any backend endpoint.
2. WHEN the Firmware receives a `SUBMIT_LOG` WebSocket action with `payload.actionType`, `payload.status`, and `payload.notes` present, THE Firmware SHALL POST `{ machineUuid: MACHINE_ID, actionType, status, notes, performedById: <user_id_from_auth> }` to `POST /api/rpi/logs/machines` with the `X-API-Key` header.
3. WHEN the `POST /api/rpi/logs/machines` call fails (non-2xx or network error), THE Firmware SHALL log the failure; no retry is required.
4. WHEN `DEV_MODE` is `false`, THE `kioskApi.submitMachineLog` HTTP function SHALL NOT be called from any component or hook.

---

### Requirement 12: Environment Configuration File

**User Story:** As a developer or system operator, I want a documented `.env.example` file, so that I can configure a new RVM deployment without hunting for required variables.

#### Acceptance Criteria

1. THE `rvm_edge_client` directory SHALL contain a file named `.env.example`.
2. THE `.env.example` file SHALL declare all required environment variable keys: `BACKEND_URL`, `MACHINE_ID`, `LOCATION`, `API_KEY`, `QR_HMAC_SECRET`, `CLI_MODE`, `DISABLE_GPIO`, `UHUBCTL_LOCATIONS`, and `UHUBCTL_PORT`.
3. THE `.env.example` file SHALL contain only placeholder values for secret keys (`API_KEY`, `QR_HMAC_SECRET`) — where a placeholder is a non-functional string that would not pass backend authentication (e.g. `your_api_key_here`).
4. THE `.env.example` file SHALL include an inline comment for each variable describing its purpose, accepted format (e.g. URL, boolean string `true`/`false`, comma-separated hub locations), and default or example value; `UHUBCTL_LOCATIONS` and `UHUBCTL_PORT` SHALL note they may be left empty if `uhubctl` is not used.
