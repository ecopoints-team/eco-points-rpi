"""
Property test for wait_for_action timeout upper bound.

**Validates: Requirements 4.1, 4.5**

Property 4: Timeout upper bound — for any timeout_seconds > 0,
wait_for_action returns within timeout_seconds + 1.0 wall-clock seconds
when the message queue remains empty.
"""
import os
import sys

os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from unittest.mock import MagicMock
from hypothesis import given, settings
from hypothesis import strategies as st
import main


@given(st.floats(min_value=0.1, max_value=2.0))
@settings(max_examples=20, deadline=10000)
def test_wait_for_action_timeout_upper_bound(timeout_seconds):
    """
    **Validates: Requirements 4.1, 4.5**

    Property 4: For any timeout_seconds in (0, 2.0], wait_for_action must
    return within timeout_seconds + 1.0 wall-clock seconds when the message
    queue is always empty (get_message returns None).
    """
    mock_bridge = MagicMock()
    mock_bridge.clients = {"mock_client"}  # non-empty so early-exit doesn't fire
    mock_bridge.get_message.return_value = None  # queue always empty

    start = time.monotonic()
    result = main.wait_for_action(mock_bridge, ["SOME_ACTION"], timeout_seconds=timeout_seconds)
    elapsed = time.monotonic() - start

    assert result is None, f"Expected None (timeout), got {result}"
    assert elapsed <= timeout_seconds + 1.0, (
        f"wait_for_action took {elapsed:.3f}s, exceeded timeout {timeout_seconds:.3f} + 1.0s"
    )
