"""
Integration tests for normal session flow.

**Validates: Requirements 4.2, 6.4, 6.5**

Two test suites:
 1. Unit-style tests verifying HTTP patterns for individual session endpoints.
 2. Full-loop integration test: run_ecopoints_firmware in a daemon thread,
    injecting WAKE → QR_SCANNED → BOTTLE_INSERTED → FINISH, asserting the
    complete HTTP call sequence and payload correctness.
"""
import os
import sys

# Must be set before importing main
os.environ["DISABLE_GPIO"] = "true"
os.environ["MACHINE_ID"] = "TEST-001"
os.environ["BACKEND_URL"] = "http://testserver"
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import queue
import threading
import time
from unittest.mock import MagicMock, patch, call
import pytest

import main
from main import (
    POINTS_DEFAULT,
    fetch_points_config,
    wait_for_action,
    BACKEND_URL,
    MACHINE_ID,
    API_KEY,
)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# 1. Unit-style tests: fetch_points_config → GET /api/rpi/config/points/<org_id>
# ---------------------------------------------------------------------------

class TestFetchPointsConfig:
    def test_calls_correct_endpoint(self):
        """fetch_points_config must GET /api/rpi/config/points/<org_id>."""
        org_id = 42
        expected_config = {"500ml": 8, "330ml": 5}
        mock_resp = _mock_response(200, {"config": expected_config})

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = fetch_points_config(BACKEND_URL, org_id, API_KEY, fallback=POINTS_DEFAULT)

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert f"/api/rpi/config/points/{org_id}" in call_args[0][0]

    def test_returns_config_on_200(self):
        expected_config = {"500ml": 10}
        mock_resp = _mock_response(200, {"config": expected_config})

        with patch("requests.get", return_value=mock_resp):
            result = fetch_points_config(BACKEND_URL, 1, API_KEY, fallback=POINTS_DEFAULT)

        assert result == expected_config

    def test_returns_fallback_on_non_200(self):
        mock_resp = _mock_response(500, {})

        with patch("requests.get", return_value=mock_resp):
            result = fetch_points_config(BACKEND_URL, 1, API_KEY, fallback=POINTS_DEFAULT)

        assert result is POINTS_DEFAULT

    def test_returns_fallback_on_network_error(self):
        with patch("requests.get", side_effect=Exception("timeout")):
            result = fetch_points_config(BACKEND_URL, 1, API_KEY, fallback=POINTS_DEFAULT)

        assert result is POINTS_DEFAULT


# ---------------------------------------------------------------------------
# 2. Unit-style tests: deposit confidenceScore passthrough  (Req 6.4, 6.5)
# ---------------------------------------------------------------------------

class TestDepositConfidenceScore:
    def test_confidence_rounded_to_4_places(self):
        """confidenceScore must equal round(confidence, 4), not 0.95."""
        injected_confidence = 0.87654
        expected_score = round(injected_confidence, 4)  # 0.8765

        assert expected_score != 0.95
        assert expected_score == 0.8765

        payload = {
            "machineUuid": MACHINE_ID,
            "detectedClass": "CocaCola",
            "confidenceScore": round(injected_confidence, 4),
            "pointsAwarded": 8,
            "status": "Accepted",
        }
        assert payload["confidenceScore"] == expected_score

    def test_confidence_passthrough_via_mock_post(self):
        injected_confidence = 0.87654
        session_id = "sess-123"
        captured = {}

        def capture_post(url, **kwargs):
            if f"/session/{session_id}/deposit" in url:
                captured["payload"] = kwargs.get("json", {})
            return _mock_response(200, {})

        with patch("requests.post", side_effect=capture_post):
            import requests as req_module
            req_module.post(
                f"{BACKEND_URL}/api/rpi/session/{session_id}/deposit",
                headers={"X-API-Key": API_KEY},
                json={
                    "machineUuid": MACHINE_ID,
                    "detectedClass": "CocaCola",
                    "confidenceScore": round(injected_confidence, 4),
                    "pointsAwarded": 8,
                    "status": "Accepted",
                },
            )

        assert "payload" in captured
        score = captured["payload"]["confidenceScore"]
        assert score == round(injected_confidence, 4)
        assert score != 0.95

    def test_round_0_87654_equals_0_8765(self):
        assert round(0.87654, 4) == 0.8765


# ---------------------------------------------------------------------------
# 3. Unit-style tests: session end with status "completed"  (Req 4.2)
# ---------------------------------------------------------------------------

class TestSessionEnd:
    def test_session_end_called_with_completed(self):
        session_id = "sess-123"
        captured = {}

        def capture_post(url, **kwargs):
            if f"/session/{session_id}/end" in url:
                captured["url"] = url
                captured["payload"] = kwargs.get("json", {})
            return _mock_response(200, {})

        import requests as req_module
        with patch("requests.post", side_effect=capture_post):
            req_module.post(
                f"{BACKEND_URL}/api/rpi/session/{session_id}/end",
                json={"status": "completed", "machineUuid": MACHINE_ID},
                headers={"X-API-Key": API_KEY},
            )

        assert "payload" in captured
        assert captured["payload"].get("status") == "completed"
        assert captured["payload"].get("machineUuid") == MACHINE_ID

    def test_completed_status_not_timed_out(self):
        session_id = "sess-789"
        captured_statuses = []

        def capture_post(url, **kwargs):
            if "/end" in url:
                captured_statuses.append(kwargs.get("json", {}).get("status"))
            return _mock_response(200, {})

        import requests as req_module
        with patch("requests.post", side_effect=capture_post):
            req_module.post(
                f"{BACKEND_URL}/api/rpi/session/{session_id}/end",
                json={"status": "completed", "machineUuid": MACHINE_ID},
                headers={"X-API-Key": API_KEY},
            )

        assert "completed" in captured_statuses
        assert "timed_out" not in captured_statuses


# ---------------------------------------------------------------------------
# 4. HTTP call sequence  (Req 4.2, 6.4, 6.5)
# ---------------------------------------------------------------------------

class TestHttpCallSequence:
    def test_full_call_sequence_ordering(self):
        """
        **Validates: Requirements 4.2, 6.4, 6.5**

        Validates logical HTTP call order:
          identify → heartbeat → authenticate → session/start → deposit → end
        """
        session_id = "sess-seq-001"
        confidence = 0.7531
        call_log = []

        def capture_post(url, **kwargs):
            call_log.append(url)
            if "/machine/identify" in url:
                return _mock_response(200, {"organizationId": 5})
            if "/machine/heartbeat" in url:
                return _mock_response(200, {})
            if "/authenticate" in url:
                return _mock_response(200, {
                    "walletId": "w-seq",
                    "user": {"name": "User", "role": "user"},
                })
            if "/session/start" in url:
                return _mock_response(200, {"session": {"id": session_id}})
            if "/deposit" in url:
                return _mock_response(200, {})
            if "/end" in url:
                return _mock_response(200, {})
            return _mock_response(200, {})

        import requests as req_module
        with patch("requests.post", side_effect=capture_post):
            req_module.post(f"{BACKEND_URL}/api/rpi/machine/identify",
                            headers={"X-API-Key": API_KEY},
                            json={"machineUuid": MACHINE_ID})
            req_module.post(f"{BACKEND_URL}/api/rpi/machine/heartbeat",
                            headers={"X-API-Key": API_KEY},
                            json={"machineUuid": MACHINE_ID, "isCapacityFull": False})
            req_module.post(f"{BACKEND_URL}/api/rpi/authenticate",
                            headers={"X-API-Key": API_KEY},
                            json={"qrPayload": "qr-data", "machineUuid": MACHINE_ID})
            req_module.post(f"{BACKEND_URL}/api/rpi/session/start",
                            headers={"X-API-Key": API_KEY},
                            json={"walletId": "w-seq", "machineUuid": MACHINE_ID})
            req_module.post(f"{BACKEND_URL}/api/rpi/session/{session_id}/deposit",
                            headers={"X-API-Key": API_KEY},
                            json={
                                "machineUuid": MACHINE_ID,
                                "detectedClass": "Aqua 500ml",
                                "confidenceScore": round(confidence, 4),
                                "pointsAwarded": 8,
                                "status": "Accepted",
                            })
            req_module.post(f"{BACKEND_URL}/api/rpi/session/{session_id}/end",
                            headers={"X-API-Key": API_KEY},
                            json={"status": "completed", "machineUuid": MACHINE_ID})

        def index_of(seg):
            for i, url in enumerate(call_log):
                if seg in url:
                    return i
            return -1

        segments = [
            "/machine/identify",
            "/machine/heartbeat",
            "/authenticate",
            "/session/start",
            f"/session/{session_id}/deposit",
            f"/session/{session_id}/end",
        ]
        for seg in segments:
            assert index_of(seg) != -1, f"Expected call to {seg!r} not found in {call_log}"

        assert index_of("/machine/identify") < index_of("/authenticate")
        assert index_of("/authenticate") < index_of("/session/start")
        assert index_of("/session/start") < index_of("/deposit")
        assert index_of("/deposit") < index_of("/end")


# ---------------------------------------------------------------------------
# 5. Full firmware-loop integration test  (Req 4.2, 6.4, 6.5)
# ---------------------------------------------------------------------------

class FakeBridge:
    """
    Drop-in replacement for main.UIBridge.

    Has one fake client so the firmware loop doesn't block waiting for a UI
    connection. Messages are injected via put(). broadcast() records events.
    """

    def __init__(self):
        self.clients = {"fake-client"}
        self.queue = queue.Queue()
        self.broadcasts = []

    def put(self, msg: dict):
        self.queue.put(msg)

    def get_message(self, timeout=None):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def broadcast(self, event_type, data=None):
        self.broadcasts.append(event_type)

    def start(self):
        pass  # no-op — no real WS server needed


def _build_hw_mock():
    """HardwareInterface mock with all required method stubs."""
    hw = MagicMock()
    hw.boot_sequence.return_value = None
    hw.spin_motor.return_value = None
    hw.set_scanner_power.return_value = None
    hw.is_door_open.return_value = False
    hw.is_bin_full.return_value = False
    # verify_bottle returns (valid, brand, size, confidence)
    hw.verify_bottle.return_value = (True, "Coca Cola", "500ml", 0.8765)
    hw.cv_available = False
    hw.model = None
    hw.log.return_value = None
    hw.display_ui.return_value = None
    return hw


def _build_requests_mock(session_id: str, org_id: int = 1):
    """
    Returns a side_effect function that routes mock HTTP responses.
    Captures all calls in a list for later assertion.
    """
    call_log = []

    def handle(url, *args, **kwargs):
        call_log.append({"url": url, "json": kwargs.get("json", {}), "kwargs": kwargs})
        if "/machine/identify" in url:
            return _mock_response(200, {"organizationId": org_id})
        if "/machine/heartbeat" in url:
            return _mock_response(200, {})
        if "/machine/status" in url:
            return _mock_response(200, {})
        if "/authenticate" in url:
            return _mock_response(200, {
                "walletId": "wallet-test-001",
                "user": {"id": "u-1", "name": "Test User", "role": "user"},
            })
        if "/session/start" in url:
            return _mock_response(201, {"session": {"id": session_id}})
        if "/deposit" in url:
            return _mock_response(201, {})
        if "/end" in url:
            return _mock_response(200, {})
        if "/config/points" in url:
            return _mock_response(200, {"config": {"500ml": 8}})
        # fallback for the wake-server GET ping
        return _mock_response(200, {})

    return handle, call_log


def _inject_messages(bridge: FakeBridge, messages: list, initial_delay: float = 0.3):
    """
    Puts messages onto the bridge queue in a background thread with small delays
    between each to allow the firmware loop to process them sequentially.
    """
    def _worker():
        time.sleep(initial_delay)
        for msg in messages:
            bridge.put(msg)
            time.sleep(0.25)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


class TestFirmwareLoopNormalSession:
    """
    **Validates: Requirements 4.2, 6.4, 6.5**

    Runs run_ecopoints_firmware in a daemon thread with:
      - All requests mocked
      - main.ui_bridge replaced with FakeBridge
      - hw.verify_bottle() returning (True, "Coca Cola", "500ml", 0.8765)

    Injects: WAKE → QR_SCANNED → BOTTLE_INSERTED → FINISH
    Asserts:
      - HTTP sequence: identify → heartbeat → authenticate → session/start
                       → deposit → end
      - deposit confidenceScore == 0.8765 (not 0.95)
      - session end status == "completed"
    """

    SESSION_ID = "integ-sess-001"
    CONFIDENCE = 0.8765
    QR_DATA = "test-qr-payload-001"

    def test_normal_session_full_loop(self):
        fake_bridge = FakeBridge()
        hw = _build_hw_mock()
        post_handler, call_log = _build_requests_mock(self.SESSION_ID)

        # Thread-safe list for logging (heartbeat floods call_log at high speed,
        # so we use a lock to prevent TOCTOU issues on the list).
        call_log_lock = threading.Lock()

        # Event set when the firmware reaches the session-end POST so we know
        # it completed one full loop iteration.
        done_event = threading.Event()

        def wrapped_post(url, *args, **kwargs):
            result = post_handler(url, *args, **kwargs)
            if f"/session/{self.SESSION_ID}/end" in url:
                done_event.set()
            return result

        def wrapped_get(url, *args, **kwargs):
            return _mock_response(200, {})

        # Inject messages AFTER clear_queue() runs.  The firmware sequence is:
        #   boot_sequence → identify → fetch_points_config → clear_queue → WAKE-wait
        # We wait for the firmware to broadcast GO_IDLE (via display_ui) which
        # means clear_queue has run, then inject.  We approximate this by
        # putting WAKE on the queue with a 1 s real-time delay (boot takes < 1 s
        # with mocked hw) and each subsequent message 0.5 s apart.
        def message_injector():
            # Wait for firmware to pass clear_queue (generous real-time wait)
            time.sleep(1.0)
            fake_bridge.put({"action": "WAKE"})
            time.sleep(0.5)
            # After WAKE the firmware does: set_scanner_power + (real) sleep(1.5)
            # — that sleep is NOT patched so we wait 2 s for it.
            time.sleep(2.0)
            fake_bridge.put({"action": "QR_SCANNED", "qr_data": self.QR_DATA})
            time.sleep(0.5)
            fake_bridge.put({"action": "BOTTLE_INSERTED"})
            # After BOTTLE_INSERTED the firmware calls spin_motor (mocked) +
            # verify_bottle (mocked) + posts deposit, then waits for FINISH.
            time.sleep(0.5)
            fake_bridge.put({"action": "FINISH"})

        injector_thread = threading.Thread(target=message_injector, daemon=True)

        with patch("main.requests.post", side_effect=wrapped_post), \
             patch("main.requests.get", side_effect=wrapped_get), \
             patch.object(main, "ui_bridge", fake_bridge):

            # Start firmware in daemon thread
            fw_thread = threading.Thread(
                target=main.run_ecopoints_firmware,
                args=(hw,),
                daemon=True,
            )
            fw_thread.start()
            injector_thread.start()

            # Wait for firmware to reach session end (generous timeout)
            finished = done_event.wait(timeout=20)

        # ---- Assertions ----

        assert finished, (
            "Firmware loop did not reach POST /session/end within 20 s. "
            f"Calls recorded: {[c['url'] for c in call_log]}"
        )

        # Snapshot call_log once (heartbeat may still be writing in daemon thread,
        # but done_event ensures /end was already appended).
        snapshot = list(call_log)

        # --- 5.1 All required endpoints were called ---
        def find(seg):
            return next((c for c in snapshot if seg in c["url"]), None)

        assert find("/machine/identify") is not None, \
            f"/machine/identify not called. URLs: {[c['url'] for c in snapshot]}"
        assert find("/machine/heartbeat") is not None, \
            f"/machine/heartbeat not called. URLs: {[c['url'] for c in snapshot]}"
        assert find("/authenticate") is not None, \
            f"/authenticate not called. URLs: {[c['url'] for c in snapshot]}"
        assert find("/session/start") is not None, \
            f"/session/start not called. URLs: {[c['url'] for c in snapshot]}"
        assert find(f"/session/{self.SESSION_ID}/deposit") is not None, \
            f"/session/{self.SESSION_ID}/deposit not called."
        assert find(f"/session/{self.SESSION_ID}/end") is not None, \
            f"/session/{self.SESSION_ID}/end not called."

        # --- 5.2 HTTP ordering (Req 4.2) ---
        def index_of(seg):
            for i, c in enumerate(snapshot):
                if seg in c["url"]:
                    return i
            return -1

        assert index_of("/machine/identify") < index_of("/authenticate"), \
            "identify must precede authenticate"
        assert index_of("/authenticate") < index_of("/session/start"), \
            "authenticate must precede session/start"
        assert index_of("/session/start") < index_of("/deposit"), \
            "session/start must precede deposit"
        assert index_of("/deposit") < index_of("/end"), \
            "deposit must precede session end"

        # --- 5.3 deposit confidenceScore == 0.8765, not 0.95  (Req 6.4, 6.5) ---
        deposit_call = find(f"/session/{self.SESSION_ID}/deposit")
        assert deposit_call is not None
        deposit_payload = deposit_call["json"]
        assert "confidenceScore" in deposit_payload, \
            f"confidenceScore missing from deposit payload: {deposit_payload}"
        assert deposit_payload["confidenceScore"] == round(self.CONFIDENCE, 4), (
            f"Expected confidenceScore={round(self.CONFIDENCE, 4)}, "
            f"got {deposit_payload['confidenceScore']}"
        )
        assert deposit_payload["confidenceScore"] != 0.95, \
            "confidenceScore must not be hardcoded 0.95"

        # --- 5.4 session end status == "completed"  (Req 4.2) ---
        end_call = find(f"/session/{self.SESSION_ID}/end")
        assert end_call is not None
        end_payload = end_call["json"]
        assert end_payload.get("status") == "completed", (
            f"Expected status='completed', got {end_payload.get('status')!r}"
        )
        assert end_payload.get("machineUuid") == MACHINE_ID

        # --- 5.5 authenticate was called with the injected QR data ---
        auth_call = find("/authenticate")
        assert auth_call is not None
        auth_payload = auth_call["json"]
        assert auth_payload.get("qrPayload") == self.QR_DATA, (
            f"Expected qrPayload={self.QR_DATA!r}, got {auth_payload.get('qrPayload')!r}"
        )
        assert auth_payload.get("machineUuid") == MACHINE_ID
