"""
Integration test: session timeout path.

**Validates: Requirements 4.2, 4.3, 4.6**

Runs run_ecopoints_firmware in a daemon thread with:
  - All hardware mocked (GPIO disabled, hw methods mocked)
  - requests mocked
  - wait_for_action patched to use timeout_seconds=2.0 default

Message sequence injected: WAKE → QR_SCANNED → BOTTLE_INSERTED
Then withholds FINISH/REPEAT_READY so wait_for_action times out.

Asserts:
  - POST /session/<id>/end called with status="timed_out"
  - ui_bridge.broadcast called with "ADVANCE_THANK_YOU"
"""
import os
import sys
import time
import threading
from unittest.mock import MagicMock, patch, call

# Must be set BEFORE importing main so module-level constants bind correctly.
os.environ["DISABLE_GPIO"] = "true"
os.environ["MACHINE_ID"] = "TEST-001"
os.environ["BACKEND_URL"] = "http://testserver"
os.environ["API_KEY"] = "test_key"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import main  # noqa: E402

# ---------------------------------------------------------------------------
# Constants matching what the firmware will use
# ---------------------------------------------------------------------------
SESSION_ID = "timeout-session-42"
WALLET_ID = "wallet-99"
BACKEND_URL = "http://testserver"
MACHINE_ID = "TEST-001"
API_KEY = "test_key"

# Short timeout so the test completes quickly.
# wait_for_action is patched to default to this value.
SHORT_TIMEOUT = 2.0
# Total wall-clock budget: timeout + generous buffer for firmware boot + HTTP overhead
TEST_BUDGET = SHORT_TIMEOUT + 15.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_mock_requests(session_id=SESSION_ID):
    """
    Returns a side_effect function for requests.post / requests.get that
    returns canned responses for each known endpoint, and records all calls.
    """
    call_log = []

    def mock_post(url, **kwargs):
        call_log.append(("POST", url, kwargs.get("json", {})))
        resp = MagicMock()
        resp.status_code = 200
        if "/machine/identify" in url:
            resp.json.return_value = {"organizationId": 1}
        elif "/machine/heartbeat" in url:
            resp.json.return_value = {}
        elif "/authenticate" in url:
            resp.json.return_value = {
                "walletId": WALLET_ID,
                "user": {"name": "Alice", "role": "user", "id": "user-1"},
            }
        elif "/session/start" in url:
            resp.json.return_value = {"session": {"id": session_id}}
        elif f"/session/{session_id}/deposit" in url:
            resp.json.return_value = {}
        elif f"/session/{session_id}/end" in url:
            resp.json.return_value = {}
        else:
            resp.json.return_value = {}
        return resp

    def mock_get(url, **kwargs):
        call_log.append(("GET", url, {}))
        resp = MagicMock()
        resp.status_code = 200
        if "/config/points" in url:
            resp.json.return_value = {"config": {"500ml": 8}}
        else:
            resp.json.return_value = {}
        return resp

    return mock_post, mock_get, call_log


def _build_mock_hw():
    """HardwareInterface mock with all required methods stubbed."""
    hw = MagicMock()
    hw.boot_sequence.return_value = None
    hw.spin_motor.return_value = None
    hw.set_scanner_power.return_value = None
    hw.is_door_open.return_value = False
    hw.is_bin_full.return_value = False
    hw.verify_bottle.return_value = (True, "Coca Cola", "500ml", 0.75)
    hw.cv_available = False
    hw.model = None
    # display_ui should not block; keep it as a no-op mock
    hw.display_ui.return_value = None
    hw.log.return_value = None
    return hw


def _inject_messages(delay_before_each=0.05):
    """
    Injects the WAKE → QR_SCANNED → BOTTLE_INSERTED message sequence into
    main.ui_bridge after a brief delay (gives the firmware thread time to reach
    each wait point).

    Does NOT inject FINISH or REPEAT_READY — this is what causes the timeout.
    """
    def _worker():
        # Give firmware thread time to start and reach the WAKE wait loop.
        time.sleep(1.0)
        main.ui_bridge.queue.put({"action": "WAKE"})

        # Give firmware time to enter QR scanning loop.
        time.sleep(0.5)
        main.ui_bridge.queue.put({"action": "QR_SCANNED", "qr_data": "test-qr-payload"})

        # Give firmware time to authenticate, start session, enter transaction loop.
        time.sleep(1.5)
        main.ui_bridge.queue.put({"action": "BOTTLE_INSERTED"})

        # Do NOT inject FINISH or REPEAT_READY — firmware will time out.

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Patched wait_for_action: same logic but default timeout = SHORT_TIMEOUT
# ---------------------------------------------------------------------------

def _short_wait_for_action(ui_bridge_arg, accepted_actions, timeout_seconds=SHORT_TIMEOUT):
    """
    Drop-in replacement for main.wait_for_action with a SHORT_TIMEOUT default.
    Preserves all original semantics (monotonic deadline, 0.5 s poll).
    """
    import queue as _queue
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not ui_bridge_arg.clients:
            return None
        msg = ui_bridge_arg.get_message(timeout=0.5)
        if msg is not None:
            action = msg.get("action")
            if action in accepted_actions:
                return action
    return None


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_session_timeout_path():
    """
    **Validates: Requirements 4.2, 4.3, 4.6**

    Full firmware integration: WAKE → QR_SCANNED → BOTTLE_INSERTED, then
    no FINISH/REPEAT_READY.  After SHORT_TIMEOUT seconds wait_for_action
    returns None; firmware must:
      1. POST /session/<id>/end with {"status": "timed_out", "machineUuid": MACHINE_ID}
      2. Call ui_bridge.broadcast("ADVANCE_THANK_YOU")
    """
    mock_post, mock_get, call_log = _build_mock_requests(SESSION_ID)
    mock_hw = _build_mock_hw()

    # Track broadcast calls
    broadcast_calls = []
    original_broadcast = main.ui_bridge.broadcast

    def recording_broadcast(event_type, data=None):
        broadcast_calls.append(event_type)
        # Call original so firmware doesn't error — but clients set is empty in test,
        # so original broadcast is effectively a no-op anyway.
        try:
            original_broadcast(event_type, data)
        except Exception:
            pass

    # Ensure ui_bridge has a fake connected client so wait_for_action doesn't
    # return None immediately due to empty clients set.
    fake_client = MagicMock()
    main.ui_bridge.clients.add(fake_client)

    # Patch broadcast to record calls
    main.ui_bridge.broadcast = recording_broadcast

    try:
        with patch("main.requests.post", side_effect=mock_post), \
             patch("main.requests.get", side_effect=mock_get), \
             patch("main.wait_for_action", side_effect=_short_wait_for_action):

            # Start firmware in daemon thread
            fw_thread = threading.Thread(
                target=main.run_ecopoints_firmware,
                args=(mock_hw,),
                daemon=True,
            )
            fw_thread.start()

            # Inject message sequence
            _inject_messages()

            # Wait long enough for: boot + QR auth + deposit + SHORT_TIMEOUT + buffer
            fw_thread.join(timeout=TEST_BUDGET)

        # -----------------------------------------------------------------------
        # Assert 1: POST /session/<id>/end with status="timed_out"  (Req 4.2, 4.6)
        # -----------------------------------------------------------------------
        end_calls = [
            (url, body)
            for method, url, body in call_log
            if method == "POST" and f"/session/{SESSION_ID}/end" in url
        ]

        assert len(end_calls) >= 1, (
            f"Expected at least 1 POST to /session/{SESSION_ID}/end, got 0.\n"
            f"All calls:\n" + "\n".join(f"  {m} {u}" for m, u, _ in call_log)
        )

        # Find the timed_out call specifically
        timed_out_calls = [
            (url, body)
            for url, body in end_calls
            if body.get("status") == "timed_out"
        ]
        assert len(timed_out_calls) >= 1, (
            f"No /session/end POST with status='timed_out' found.\n"
            f"end calls: {end_calls}"
        )

        url, body = timed_out_calls[0]
        assert body.get("machineUuid") == MACHINE_ID, (
            f"machineUuid mismatch: expected {MACHINE_ID!r}, got {body.get('machineUuid')!r}"
        )

        # -----------------------------------------------------------------------
        # Assert 2: ADVANCE_THANK_YOU broadcast  (Req 4.3)
        # -----------------------------------------------------------------------
        assert "ADVANCE_THANK_YOU" in broadcast_calls, (
            f"ADVANCE_THANK_YOU not broadcast. Broadcast calls: {broadcast_calls}"
        )

    finally:
        # Clean up: remove fake client and restore original broadcast
        main.ui_bridge.clients.discard(fake_client)
        main.ui_bridge.broadcast = original_broadcast
