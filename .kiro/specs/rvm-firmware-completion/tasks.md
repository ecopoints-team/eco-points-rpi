# Implementation Plan: rvm-firmware-completion

## Overview

Completes the 12 production gaps in `rvm_edge_client/main.py` and `ui/src/`. All changes are additive or corrective — no architectural shifts. Implementation language: **Python** (firmware) and **TypeScript/React Native** (UI).

---

## Tasks

- [x] 1. Add heartbeat daemon thread to firmware
  - [x] 1.1 Define `_heartbeat_worker` and `start_heartbeat_thread` in `main.py`
    - Add `_heartbeat_worker(hw, backend_url, machine_id, api_key, interval=30)` function that POSTs `{machineUuid, isCapacityFull}` to `POST /api/rpi/machine/heartbeat` every 30 s with a 10 s request timeout; swallows all exceptions and logs failures; never raises
    - Add `start_heartbeat_thread(hw)` that creates a `daemon=True` thread running `_heartbeat_worker` and starts it; returns the thread
    - Call `start_heartbeat_thread(hw)` immediately after `hw.boot_sequence()` in `run_ecopoints_firmware`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 Write property test for heartbeat payload schema (Property 1)
    - **Property 1: Heartbeat liveness** — for any `bool` value of `is_bin_full`, the serialized heartbeat payload contains `machineUuid` (str) and `isCapacityFull` (bool) and passes backend schema validation
    - Use `hypothesis` `@given(st.booleans())` to vary `is_bin_full`; mock `requests.post`; assert payload keys and types on every call
    - **Validates: Requirements 1.1, 1.2**

- [x] 2. Implement bin-full machine status sync
  - [x] 2.1 Add `_sync_bin_status` method and wire into `_monitor_bin_full`
    - Add `_sync_bin_status(self, full: bool)` to `HardwareInterface`: spawns a `daemon=True` thread that POSTs `{machineUuid: MACHINE_ID, isCapacityFull: full}` to `POST /api/rpi/machine/status` with 10 s timeout; logs failures; does not retry
    - In `_monitor_bin_full`, on the `False→True` edge: call `self._sync_bin_status(True)` then `ui_bridge.broadcast("SET_BIN_FULL")`
    - On the `True→False` edge: call `self._sync_bin_status(False)` then `ui_bridge.broadcast("CLEAR_BIN_FULL")`
    - Do NOT call `_sync_bin_status` on every poll tick — only on edge transitions
    - Preserve existing 50-poll **LOW** / 5-poll **HIGH** debounce thresholds unchanged — curtain sensor is inverted (LOW = blocked/full, HIGH = clear)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.2 Write property test for bin-full edge-only POST (Property 5)
    - **Property 5: Bin-full status monotonicity on edge** — `_sync_bin_status` is called exactly once on False→True and once on True→False; never on repeated same-state polls
    - Use `hypothesis` to drive arbitrary sequences of HIGH/LOW poll values; count `_sync_bin_status` calls via mock; assert call count equals number of edge transitions
    - **Validates: Requirements 2.1, 2.3, 2.5**

- [x] 3. Implement points configuration fetch at startup
  - [x] 3.1 Add `POINTS_DEFAULT` dict and `fetch_points_config` function
    - Define `POINTS_DEFAULT: dict[str, int]` at module level covering all 21 size tokens: `extra small`, `xs`, `small`, `s`, `medium`, `m`, `large`, `l`, `1000ml`, `750ml`, `551ml`, `600ml`, `550ml`, `500ml`, `351ml`, `350ml`, `330ml`, `290ml`, `289ml`, `250ml`, `125ml`
    - Add `fetch_points_config(backend_url, org_id, api_key, fallback)` that calls `GET /api/rpi/config/points/<org_id>` with 10 s timeout; returns `response["config"]` dict on HTTP 200 + `config` key present; returns `fallback` on any error; logs warning on failure
    - _Requirements: 3.3, 3.4_

  - [x] 3.2 Call `POST /api/rpi/machine/identify` at startup to obtain `org_id`, then call `fetch_points_config`
    - At startup in `run_ecopoints_firmware` (after `boot_sequence()`, before the main `while True` loop), call `POST /api/rpi/machine/identify` with `{machineUuid: MACHINE_ID}` and `X-API-Key` header; extract `organizationId` from response
    - Pass `org_id` to `fetch_points_config`; store result as `points_config` local variable
    - Replace the existing inline `if/elif` points mapping block in the deposit path with a single `points_config.get(size_token, POINTS_DEFAULT.get(size_token, 5))` lookup where `size_token` is the last word of `best_class` lowercased
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.3 Write property test for points fallback completeness (Property 7)
    - **Property 7: Points config fallback completeness** — for every size token that `verify_bottle()` can return, `POINTS_DEFAULT.get(token)` returns a non-zero integer
    - Use `hypothesis` `@given(st.sampled_from([list of all 21 tokens]))` to assert `POINTS_DEFAULT[token] > 0` for every token
    - **Validates: Requirements 3.3, 3.4**

- [ ] 4. Checkpoint — run existing tests, verify startup sequence
  - Ensure `python main.py` boots without error with `DISABLE_GPIO=true CLI_MODE=true`
  - Ensure `POINTS_DEFAULT` and `fetch_points_config` callable from REPL

- [x] 5. Implement session timeout with `wait_for_action`
  - [x] 5.1 Add `wait_for_action` helper function
    - Add `wait_for_action(ui_bridge, accepted_actions, timeout_seconds=300.0) -> str | None` in `main.py`
    - Use `time.monotonic()` for deadline; poll `ui_bridge.get_message(timeout=0.5)` in a loop until deadline or accepted action received
    - Return action string on match; return `None` on timeout or when `ui_bridge.clients` is empty
    - _Requirements: 4.1, 4.5_

  - [x] 5.2 Replace raw `while True` deposit wait loops with `wait_for_action`
    - Replace the `REPEAT_READY`/`FINISH` wait loop after `VERIFY_FAIL` (rejection path) with `action = wait_for_action(ui_bridge, ["REPEAT_READY", "FINISH", "CANCEL"])`
    - Replace the `REPEAT_READY`/`FINISH` wait loop after `VERIFY_SUCCESS` (acceptance path) with `action = wait_for_action(ui_bridge, ["REPEAT_READY", "FINISH"])`
    - On `None` return: call `POST /api/rpi/session/<session_id>/end` with `{"status": "timed_out", "machineUuid": MACHINE_ID}`; broadcast `ADVANCE_THANK_YOU`; set `transacting = False`; log failure if end call fails but continue
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

  - [x] 5.3 Write property test for timeout upper bound (Property 4)
    - **Property 4: Timeout upper bound** — for any `timeout_seconds > 0`, `wait_for_action` returns within `timeout_seconds + 1.0` wall-clock seconds when the message queue remains empty
    - Use `hypothesis` `@given(st.floats(min_value=0.1, max_value=2.0))` to vary timeout; inject mock `UIBridge` that always returns `None`; measure wall-clock elapsed; assert `elapsed <= timeout + 1.0`
    - **Validates: Requirements 4.1, 4.5**

- [x] 6. Add stepper motor GPIO pin control
  - [x] 6.1 Define motor pin constants and update `_setup_gpio` and `shutdown_gpio`
    - Replace `PIN_MOTOR_RELAY = 24` with the following constants at the top of the pin-assignment block:
      ```python
      PIN_MOTOR_PULSE  = 12  # BCM 12 — step pulse
      PIN_MOTOR_DIR    = 16  # BCM 16 — direction
      PIN_MOTOR_ENABLE = 17  # BCM 17 — driver enable, active-LOW
      PIN_MOTOR_HOME   = 6   # BCM 6  — homing sensor SW2
      PIN_IN_PROGRESS  = 26  # BCM 26 — In Progress indicator, active-LOW
      PIN_STROBE       = 22  # BCM 22 — Strobe light
      ```
    - In `_setup_gpio`, configure all motor pins: `PIN_MOTOR_ENABLE` OUT initial HIGH (disabled), `PIN_MOTOR_PULSE` OUT initial LOW, `PIN_MOTOR_DIR` OUT initial LOW, `PIN_IN_PROGRESS` OUT initial HIGH (off, active-LOW), `PIN_STROBE` OUT initial LOW (off), `PIN_MOTOR_HOME` IN with pull-up
    - In `shutdown_gpio`, drive `PIN_MOTOR_ENABLE` HIGH (disable driver), `PIN_IN_PROGRESS` HIGH (off), `PIN_STROBE` LOW (off) before `GPIO.cleanup()`
    - Remove the old `PIN_BOTTLE_INSERTED = 17` interrupt setup — BCM 17 is now the motor enable output; bottle insertion is now detected via the homing sensor (BCM 6) and camera only
    - _Requirements: 5.1, 5.2, 5.6, 5.7_

  - [x] 6.2 Implement `spin_motor` with stepper PULSE/DIR/ENABLE + homing sensor
    - Replace the `time.sleep(duration)` stub with stepper motor logic:
      1. Set `PIN_MOTOR_DIR` to desired direction (HIGH for forward)
      2. Assert `PIN_MOTOR_ENABLE` LOW (enable driver, active-LOW)
      3. Assert `PIN_IN_PROGRESS` LOW (turn on indicator, active-LOW) and `PIN_STROBE` HIGH
      4. Loop `steps` times: pulse `PIN_MOTOR_PULSE` HIGH for 0.5 ms then LOW for 0.5 ms; break early if `PIN_MOTOR_HOME` reads LOW (homing position reached)
      5. In `finally`: assert `PIN_MOTOR_ENABLE` HIGH (disable), `PIN_IN_PROGRESS` HIGH (off), `PIN_STROBE` LOW (off)
    - Default `steps=200`; simulation fallback when GPIO unavailable: `time.sleep(steps * 0.001)`
    - Wrap entire GPIO sequence in try/except; log errors and always run `finally` block
    - _Requirements: 5.3, 5.4, 5.5_

- [x] 7. Implement YOLO confidence score passthrough
  - [x] 7.1 Change `verify_bottle` return to 4-tuple
    - Update return type annotation to `tuple[bool, str, str, float]`
    - On success path: return `(True, brand, size, best_conf)` — `best_conf` is already computed as `max([conf for name, conf in detections if name == best_class])`
    - On all failure/invalid paths: return `(False, "None", "None", 0.0)`
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 7.2 Update all `verify_bottle` call sites and deposit payload
    - Change `is_valid, brand_name, size_category = hw.verify_bottle()` to `is_valid, brand_name, size_category, confidence = hw.verify_bottle()`
    - In deposit payload: replace `"confidenceScore": 0.95` with `"confidenceScore": round(confidence, 4)`
    - _Requirements: 6.4, 6.5_

  - [x] 7.3 Write property test for confidence passthrough (Property 2)
    - **Property 2: Confidence passthrough** — for any float `conf` in `[0.0, 1.0]`, if `verify_bottle` returns `(True, brand, size, conf)` then the deposit payload's `confidenceScore` equals `round(conf, 4)` and is never a hardcoded literal
    - Use `hypothesis` `@given(st.floats(min_value=0.0, max_value=1.0))` to inject synthetic detections; assert deposit payload `confidenceScore == round(conf, 4)`
    - **Validates: Requirements 6.3, 6.4, 6.5**

- [x] 8. Checkpoint — verify firmware changes compile and mock-run cleanly
  - Run `python -c "import main"` with `DISABLE_GPIO=true`; confirm no import errors
  - Confirm `verify_bottle` returns 4-tuple in simulation fallback path

- [x] 9. Fix `useKioskTimer` FINISH guard
  - [x] 9.1 Remove `DEV_MODE` guard from FINISH send in `useKioskTimer.ts`
    - In `useKioskTimer.ts`, inside the `setTimeout` callback for `ACCEPTED`/`REJECTED` screens, remove the `if (!DEV_MODE)` block; call `sendGPIOEvent({ action: 'FINISH' })` unconditionally
    - Ensure `sendGPIOEvent` call remains **before** `dispatch(action)` call
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 10. Fix `GO_IDLE` vs `SYSTEM_CLEAR` event at idle entry
  - [x] 10.1 Change first `SYSTEM_CLEAR` broadcast to `GO_IDLE` in `main.py`
    - Locate the `hw.display_ui("Press Start Button", "SYSTEM_CLEAR")` call at the top of the idle wait block (before the WAKE polling loop, ~line 338)
    - Change the event argument from `"SYSTEM_CLEAR"` to `"GO_IDLE"` so the UI transitions to the IDLE screen (dimmed, waiting for tap) rather than hard-resetting to START
    - The `SYSTEM_CLEAR` broadcast after session end (after `ADVANCE_THANK_YOU`) remains unchanged
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

- [x] 11. QR scan wiring verification and annotation
  - [x] 11.1 Annotate `QRScanScreen.tsx` production path
    - Verify lines ~56–58 in `QRScanScreen.tsx` call `sendGPIOEvent({ action: 'QR_SCANNED', qr_data: data })` in the `else` (non-DEV_MODE) branch — no logic change required
    - Add comment `// Production path: routes QR data to firmware via WebSocket` above the `sendGPIOEvent` call
    - Add comment `// DEV_MODE only: mock auth — not active in production (DEV_MODE=false)` above the `loginWithQR` call
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 12. Remove dead code from UI
  - [x] 12.1 Delete `BinFullScreen.tsx` and verify no imports remain
    - Delete `ui/src/screens/BinFullScreen.tsx`
    - Search `ui/` for any `import.*BinFullScreen` references; remove if found (App.tsx already does not import it)
    - _Requirements: 10.1, 10.2_

  - [x] 12.2 Clean up `kioskApi.ts` mock functions
    - Remove `getVerificationResult` export and its implementation from `kioskApi.ts`
    - Remove `getSystemStatus` export and its implementation from `kioskApi.ts`
    - Add comment `// DEV_MODE only — not called in production (DEV_MODE=false)` immediately above `export async function loginWithQR`
    - _Requirements: 10.3, 10.4_

- [ ] 13. Fix admin log routing via WebSocket
  - [x] 13.1 Remove `submitMachineLog` direct HTTP call from production path and add DEV_MODE guard comment
    - `AdminNotesScreen.tsx` already calls `sendGPIOEvent({ action: 'SUBMIT_LOG', payload: {...} })` — no logic change required; verify this is the only submission path
    - Add comment `// DEV_MODE only — production routes through sendGPIOEvent('SUBMIT_LOG')` above `submitMachineLog` in `kioskApi.ts`; keep the function body intact for DEV_MODE use
    - Verify `main.py` SUBMIT_LOG handler (lines ~448 area) routes to `POST /api/rpi/logs/machines` with `X-API-Key` header — no change required, already correct
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [ ] 13.2 Write unit test for admin log routing (Property 9)
    - **Property 9: No direct UI-to-backend HTTP for admin logs** — assert `submitMachineLog` is never called in the `AdminNotesScreen` `handleConfirm` path when `DEV_MODE=false`; assert `sendGPIOEvent` is called with `action: 'SUBMIT_LOG'`
    - Mock `sendGPIOEvent` and `submitMachineLog`; render `AdminNotesScreen` with `DEV_MODE=false`; simulate confirm press; assert `sendGPIOEvent` call count === 1, `submitMachineLog` call count === 0
    - **Validates: Requirements 11.1, 11.4**

- [x] 14. Create `.env.example`
  - [x] 14.1 Create `rvm_edge_client/.env.example` with all 9 keys
    - Create file at `rvm_edge_client/.env.example` with variables: `BACKEND_URL`, `MACHINE_ID`, `LOCATION`, `API_KEY`, `QR_HMAC_SECRET`, `CLI_MODE`, `DISABLE_GPIO`, `UHUBCTL_LOCATIONS`, `UHUBCTL_PORT`
    - Each variable has an inline comment describing purpose, accepted format, and example/default value
    - `API_KEY` and `QR_HMAC_SECRET` use placeholder strings (`your_api_key_here`, `your_qr_hmac_secret_here`) — non-functional values that will not pass backend auth
    - `UHUBCTL_LOCATIONS` and `UHUBCTL_PORT` comments note they may be left empty if `uhubctl` is not used
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [ ] 15. Integration test: full session flow with mocked GPIO and requests
  - [x] 15.1 Write integration test for normal session (completed)
    - Start firmware loop with `DISABLE_GPIO=true`, mock `requests` module
    - Inject WS messages: `WAKE` → `QR_SCANNED` → `BOTTLE_INSERTED` → `FINISH`
    - Assert HTTP call sequence: `/machine/identify` → `/machine/heartbeat` → `/authenticate` → `/session/start` → `/session/<id>/deposit` → `/session/<id>/end`
    - Assert deposit payload `confidenceScore` matches injected YOLO confidence (not `0.95`)
    - Assert session end called with `status: "completed"`
    - _Requirements: 4.2, 6.4, 6.5_

  - [x] 15.2 Write integration test for session timeout path
    - Inject `WAKE` → `QR_SCANNED` → `BOTTLE_INSERTED`, then withhold `FINISH`/`REPEAT_READY` for `timeout_seconds + 1`
    - Assert `POST /session/<id>/end` called with `status: "timed_out"`
    - Assert `ADVANCE_THANK_YOU` broadcast sent
    - **Validates: Requirements 4.2, 4.3, 4.6**

  - [x] 15.3 Write integration test for heartbeat thread liveness
    - Mock `requests.post`; start `start_heartbeat_thread` with `interval=1`; sleep 3.5 s; assert `requests.post` called with `/machine/heartbeat` at least 3 times
    - **Validates: Requirements 1.1, 1.2**

- [ ] 16. Final checkpoint — all tests pass
  - Run `hypothesis`-based property tests: `pytest tests/ -x`
  - Run integration tests with mocked GPIO: `pytest tests/integration/ -x`
  - Ensure `python main.py` boots cleanly with `DISABLE_GPIO=true CLI_MODE=true`

---

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use `hypothesis` library (add to `requirements.txt` if not present)
- Integration tests use `pytest` + `unittest.mock.patch` for `requests` and GPIO stubs
- Tasks 1–8 are firmware-only (Python); tasks 9–13 are UI-only (TypeScript)
- Task 14 is config (no runtime logic); task 15 is test-only
- All 10 Correctness Properties from design are covered: P1→1.2, P2→7.3, P3→15.2, P4→5.3, P5→2.2, P6→6.1 (unit), P7→3.3, P8→9.1 (unit), P9→13.2, P10→12.1

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "6.1"] },
    { "id": 1, "tasks": ["2.1", "3.2", "5.1", "6.2", "7.1"] },
    { "id": 2, "tasks": ["5.2", "7.2", "1.2", "2.2", "3.3"] },
    { "id": 3, "tasks": ["5.3", "7.3", "9.1", "10.1", "11.1", "12.1", "12.2"] },
    { "id": 4, "tasks": ["13.1", "14.1"] },
    { "id": 5, "tasks": ["13.2", "15.1", "15.2", "15.3"] }
  ]
}
```
