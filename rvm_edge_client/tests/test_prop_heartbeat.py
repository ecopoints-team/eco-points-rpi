"""
Property test for heartbeat payload schema.

**Validates: Requirements 1.1, 1.2**

Property 1: Heartbeat liveness — for any bool value of is_bin_full,
the serialized heartbeat payload contains machineUuid (str) and
isCapacityFull (bool) and passes backend schema validation.
"""
import os
import sys

os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from hypothesis import given, settings
from hypothesis import strategies as st
import main


@given(st.booleans())
@settings(max_examples=50)
def test_heartbeat_payload_schema(is_bin_full):
    """
    **Validates: Requirements 1.1, 1.2**

    For any bool value of is_bin_full, the heartbeat payload sent to
    POST /api/rpi/machine/heartbeat must contain:
      - machineUuid: str
      - isCapacityFull: bool matching is_bin_full
    """
    mock_hw = MagicMock()
    mock_hw.is_bin_full.return_value = is_bin_full

    mock_response = MagicMock()
    mock_response.status_code = 200

    # Capture the first POST call then break the infinite loop via StopIteration.
    # _heartbeat_worker swallows all exceptions, so we raise from time.sleep instead
    # to exit after the first requests.post call completes.
    posted_calls = []

    def capture_post(*args, **kwargs):
        posted_calls.append(kwargs)
        return mock_response

    sleep_calls = [0]

    def break_after_first_sleep(seconds):
        sleep_calls[0] += 1
        raise StopIteration

    with patch("main.requests.post", side_effect=capture_post), \
         patch("main.time.sleep", side_effect=break_after_first_sleep):
        try:
            main._heartbeat_worker(
                mock_hw,
                "http://localhost:5000",
                "TEST-001",
                "test_key",
                interval=0,
            )
        except StopIteration:
            pass

    assert len(posted_calls) >= 1, "requests.post was never called"

    payload = posted_calls[0].get("json", {})

    assert "machineUuid" in payload, f"machineUuid missing from payload: {payload}"
    assert isinstance(payload["machineUuid"], str), (
        f"machineUuid must be str, got {type(payload['machineUuid'])}"
    )
    assert "isCapacityFull" in payload, f"isCapacityFull missing from payload: {payload}"
    assert isinstance(payload["isCapacityFull"], bool), (
        f"isCapacityFull must be bool, got {type(payload['isCapacityFull'])}"
    )
    assert payload["isCapacityFull"] == is_bin_full, (
        f"isCapacityFull={payload['isCapacityFull']} != is_bin_full={is_bin_full}"
    )
