"""
Integration test: heartbeat thread liveness.

**Validates: Requirements 1.1, 1.2**

Starts _heartbeat_worker directly with interval=1 s, sleeps 3.5 s,
asserts requests.post was called at least 3 times with /machine/heartbeat.
"""
import os
import sys
import time
import threading
from unittest.mock import MagicMock, patch

# Set env vars BEFORE importing main so module-level constants are correct.
os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import main  # noqa: E402  (must come after env vars are set)


def test_heartbeat_thread_fires_at_least_3_times_in_3_5_seconds():
    """
    **Validates: Requirements 1.1, 1.2**

    _heartbeat_worker with interval=1 must POST to /api/rpi/machine/heartbeat
    at least 3 times within 3.5 seconds (fires at ~1 s, ~2 s, ~3 s).
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

    # Req 1.1: at least 3 POSTs in 3.5 s with interval=1
    assert mock_post.call_count >= 3, (
        f"Expected >= 3 heartbeat POSTs, got {mock_post.call_count}"
    )

    # Req 1.1: every call targets /machine/heartbeat
    urls = [
        (c.args[0] if c.args else c.kwargs.get("url", ""))
        for c in mock_post.call_args_list
    ]
    assert any("/machine/heartbeat" in url for url in urls), (
        f"No call contained /machine/heartbeat. URLs seen: {urls}"
    )

    # Req 1.2: payload contains machineUuid (str) and isCapacityFull (bool)
    for c in mock_post.call_args_list:
        payload = c.kwargs.get("json", {})
        assert "machineUuid" in payload, f"machineUuid missing from payload: {payload}"
        assert isinstance(payload["machineUuid"], str), (
            f"machineUuid must be str, got {type(payload['machineUuid'])}"
        )
        assert "isCapacityFull" in payload, (
            f"isCapacityFull missing from payload: {payload}"
        )
        assert isinstance(payload["isCapacityFull"], bool), (
            f"isCapacityFull must be bool, got {type(payload['isCapacityFull'])}"
        )
