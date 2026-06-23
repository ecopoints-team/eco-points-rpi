"""
Integration test: heartbeat thread liveness.

**Validates: Requirements 1.1, 1.2**

Starts _heartbeat_worker directly with interval=1 s, sleeps 3.5 s,
asserts requests.post was called at least 3 times with the correct endpoint.
"""
import os
import sys
import time
import threading
from unittest.mock import MagicMock, patch, call

# Set env vars BEFORE importing main so module-level constants are correct.
os.environ["DISABLE_GPIO"] = "true"
os.environ["MACHINE_ID"] = "TEST-001"
os.environ["BACKEND_URL"] = "http://localhost:5000"
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main  # noqa: E402  (must come after env vars are set)


def test_heartbeat_thread_fires_at_least_3_times_in_3_5_seconds():
    """
    **Validates: Requirements 1.1, 1.2**

    _heartbeat_worker running with interval=1 must POST to
    /api/rpi/machine/heartbeat at least 3 times within 3.5 seconds.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_hw = MagicMock()
    mock_hw.is_bin_full.return_value = False

    with patch("main.requests.post", return_value=mock_response) as mock_post:
        t = threading.Thread(
            target=main._heartbeat_worker,
            args=(mock_hw, "http://localhost:5000", "TEST-001", "test_key", 1),
            daemon=True,
        )
        t.start()

        time.sleep(3.5)

    # At least 3 calls in 3.5 s with interval=1 (fires at ~1 s, ~2 s, ~3 s)
    assert mock_post.call_count >= 3, (
        f"Expected >= 3 heartbeat POSTs, got {mock_post.call_count}"
    )

    # At least one call targeted the /machine/heartbeat endpoint
    urls = [c.args[0] if c.args else c.kwargs.get("url", "") for c in mock_post.call_args_list]
    assert any("/machine/heartbeat" in url for url in urls), (
        f"No call contained /machine/heartbeat. URLs seen: {urls}"
    )


def test_heartbeat_post_contains_required_payload_fields():
    """
    **Validates: Requirements 1.1, 1.2**

    Every heartbeat POST must include machineUuid (str) and
    isCapacityFull (bool) in its JSON body.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_hw = MagicMock()
    mock_hw.is_bin_full.return_value = False

    with patch("main.requests.post", return_value=mock_response) as mock_post:
        t = threading.Thread(
            target=main._heartbeat_worker,
            args=(mock_hw, "http://localhost:5000", "TEST-001", "test_key", 1),
            daemon=True,
        )
        t.start()

        time.sleep(1.5)  # Wait for at least 1 call

    assert mock_post.call_count >= 1, "requests.post was never called"

    for c in mock_post.call_args_list:
        payload = c.kwargs.get("json", {})
        assert "machineUuid" in payload, f"machineUuid missing: {payload}"
        assert isinstance(payload["machineUuid"], str), (
            f"machineUuid must be str, got {type(payload['machineUuid'])}"
        )
        assert "isCapacityFull" in payload, f"isCapacityFull missing: {payload}"
        assert isinstance(payload["isCapacityFull"], bool), (
            f"isCapacityFull must be bool, got {type(payload['isCapacityFull'])}"
        )
