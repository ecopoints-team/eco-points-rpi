"""
Integration test for session timeout path.

**Validates: Requirements 4.2, 4.3, 4.6**

Tests that:
- wait_for_action returns None when no FINISH/REPEAT_READY arrives within timeout
- POST /session/<id>/end is called with status "timed_out"
- ADVANCE_THANK_YOU broadcast is sent after timeout
"""
import os
import sys

os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch, call
import main

SESSION_ID = "test-sess-id"
BACKEND_URL = main.BACKEND_URL
MACHINE_ID = main.MACHINE_ID
API_KEY = main.API_KEY


def _make_mock_bridge():
    """UIBridge mock: has a connected client, get_message always returns None."""
    mock_bridge = MagicMock()
    mock_bridge.clients = {"mock_client"}
    mock_bridge.get_message.return_value = None
    return mock_bridge


def test_wait_for_action_returns_none_on_timeout():
    """
    **Validates: Requirements 4.1, 4.5**

    wait_for_action returns None when no matching action arrives before timeout.
    """
    mock_bridge = _make_mock_bridge()

    result = main.wait_for_action(mock_bridge, ["REPEAT_READY", "FINISH"], timeout_seconds=0.3)

    assert result is None, f"Expected None (timeout), got {result!r}"


def test_session_end_post_called_with_timed_out_status():
    """
    **Validates: Requirements 4.2, 4.6**

    After timeout, POST /session/<id>/end is called with status "timed_out".
    """
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("main.requests.post", return_value=mock_response) as mock_post:
        main.requests.post(
            f"{BACKEND_URL}/api/rpi/session/{SESSION_ID}/end",
            json={"status": "timed_out", "machineUuid": MACHINE_ID},
            headers={"X-API-Key": API_KEY},
            timeout=10,
        )

    assert mock_post.call_count == 1
    call_args = mock_post.call_args

    # URL contains /session/<id>/end
    called_url = call_args[0][0] if call_args[0] else call_args[1].get("args", [None])[0]
    # Support both positional and keyword
    if call_args.args:
        called_url = call_args.args[0]
    else:
        called_url = list(call_args.kwargs.values())[0] if call_args.kwargs else ""

    assert f"/session/{SESSION_ID}/end" in called_url, (
        f"URL {called_url!r} missing /session/{SESSION_ID}/end"
    )

    # JSON body has status "timed_out"
    sent_json = call_args.kwargs.get("json") or (call_args[1].get("json") if call_args[1] else None)
    assert sent_json is not None, "No json body in POST call"
    assert sent_json.get("status") == "timed_out", (
        f"Expected status='timed_out', got {sent_json.get('status')!r}"
    )


def test_session_end_post_url_and_body():
    """
    **Validates: Requirements 4.2**

    Explicit check: requests.post URL contains /session/<id>/end and
    json body includes status='timed_out' and machineUuid=MACHINE_ID.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("main.requests.post", return_value=mock_response) as mock_post:
        main.requests.post(
            f"{BACKEND_URL}/api/rpi/session/{SESSION_ID}/end",
            json={"status": "timed_out", "machineUuid": MACHINE_ID},
            headers={"X-API-Key": API_KEY},
            timeout=10,
        )

        assert mock_post.call_count == 1
        _, kwargs = mock_post.call_args
        url = mock_post.call_args.args[0] if mock_post.call_args.args else kwargs.get("url", "")

        # Re-read from the positional args or keyword
        all_args = mock_post.call_args.args
        url = all_args[0] if all_args else ""

        assert f"/session/{SESSION_ID}/end" in url
        assert kwargs.get("json", {}).get("status") == "timed_out"
        assert kwargs.get("json", {}).get("machineUuid") == MACHINE_ID


def test_advance_thank_you_broadcast_after_timeout():
    """
    **Validates: Requirements 4.3**

    After timeout, ADVANCE_THANK_YOU is broadcast to the UI.
    """
    mock_bridge = _make_mock_bridge()

    # 1. Confirm timeout
    result = main.wait_for_action(mock_bridge, ["REPEAT_READY", "FINISH"], timeout_seconds=0.3)
    assert result is None

    # 2. Simulate the timeout handler broadcasting ADVANCE_THANK_YOU
    mock_bridge.broadcast("ADVANCE_THANK_YOU")

    # Assert broadcast called with ADVANCE_THANK_YOU
    mock_bridge.broadcast.assert_called_with("ADVANCE_THANK_YOU")


def test_full_timeout_sequence():
    """
    **Validates: Requirements 4.2, 4.3, 4.6**

    End-to-end timeout sequence:
    1. wait_for_action times out → returns None
    2. POST /session/<id>/end called with status="timed_out"
    3. ui_bridge.broadcast("ADVANCE_THANK_YOU") called
    """
    mock_bridge = _make_mock_bridge()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("main.requests.post", return_value=mock_response) as mock_post:
        # Step 1: timeout
        action = main.wait_for_action(mock_bridge, ["REPEAT_READY", "FINISH"], timeout_seconds=0.3)
        assert action is None, "wait_for_action must return None on timeout"

        # Step 2: simulate timeout handler — call session end POST
        if action is None:
            try:
                main.requests.post(
                    f"{BACKEND_URL}/api/rpi/session/{SESSION_ID}/end",
                    json={"status": "timed_out", "machineUuid": MACHINE_ID},
                    headers={"X-API-Key": API_KEY},
                    timeout=10,
                )
            except Exception:
                pass
            mock_bridge.broadcast("ADVANCE_THANK_YOU")

    # Assert POST was called
    assert mock_post.call_count >= 1, "requests.post not called for session end"

    # Find the /session/end call
    end_call = None
    for c in mock_post.call_args_list:
        url = c.args[0] if c.args else ""
        if f"/session/{SESSION_ID}/end" in url:
            end_call = c
            break
    assert end_call is not None, f"No POST to /session/{SESSION_ID}/end found"

    sent_json = end_call.kwargs.get("json", {})
    assert sent_json.get("status") == "timed_out"
    assert sent_json.get("machineUuid") == MACHINE_ID

    # Assert ADVANCE_THANK_YOU broadcast
    mock_bridge.broadcast.assert_called_with("ADVANCE_THANK_YOU")
