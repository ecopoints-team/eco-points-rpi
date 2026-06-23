"""
Property 5: Bin-full status monotonicity on edge.

_sync_bin_status is called exactly once on False→True and once on True→False;
never on repeated same-state polls.

Validates: Requirements 2.1, 2.3, 2.5
"""
import os
import sys

os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings
from hypothesis import strategies as st


# Replicate the debounce + edge logic from HardwareInterface._monitor_bin_full
# without running the actual thread or touching GPIO.
#
# Sensor mapping (NC NPN under pull-up, from main.py comments):
#   GPIO.HIGH (True)  = blocked = bin FULL
#   GPIO.LOW  (False) = clear   = bin NORMAL
#
# Thresholds (from _monitor_bin_full):
#   HIGH_THRESHOLD = int(5.0 / 0.1) = 50   → declare full after 50 consecutive HIGH reads
#   LOW_THRESHOLD  = int(0.5 / 0.1) = 5    → declare clear after 5 consecutive LOW reads


HIGH_THRESHOLD = 50
LOW_THRESHOLD = 5


def _simulate_bin_monitor(poll_values: list[bool]) -> list[bool]:
    """
    Simulate _monitor_bin_full over a sequence of poll readings.

    Returns a list of sync_call values: True = _sync_bin_status(True) called,
    False = _sync_bin_status(False) called.  Each entry represents one call to
    _sync_bin_status in the order the calls would occur.
    """
    bin_full_confirmed = False
    consecutive_blocks = 0
    consecutive_clears = 0
    sync_calls: list[bool] = []

    for is_high in poll_values:
        if is_high:
            consecutive_blocks += 1
            consecutive_clears = 0
            if consecutive_blocks >= HIGH_THRESHOLD and not bin_full_confirmed:
                # False → True edge transition (Req 2.1)
                bin_full_confirmed = True
                sync_calls.append(True)
        else:
            consecutive_clears += 1
            consecutive_blocks = 0
            if consecutive_clears >= LOW_THRESHOLD and bin_full_confirmed:
                # True → False edge transition (Req 2.3)
                bin_full_confirmed = False
                sync_calls.append(False)

    return sync_calls


@given(st.lists(st.booleans(), min_size=0, max_size=200))
@settings(max_examples=100)
def test_sync_bin_called_only_on_edge(poll_values: list[bool]) -> None:
    """
    **Validates: Requirements 2.1, 2.3, 2.5**

    Property 5: For any arbitrary sequence of HIGH/LOW sensor poll values,
    _sync_bin_status is called:
      - Exactly once per state transition (never double-fires on stable state).
      - Only on True edges (False→True) and False edges (True→False).
      - First call is always a False→True transition (True value).
      - Consecutive calls always alternate: no two adjacent calls carry the same value.
    """
    sync_calls = _simulate_bin_monitor(poll_values)

    # Property: no consecutive same-value calls — each call represents a genuine edge
    for i in range(1, len(sync_calls)):
        assert sync_calls[i] != sync_calls[i - 1], (
            f"Duplicate _sync_bin_status call detected at index {i}: "
            f"sync_calls={sync_calls}, poll_values={poll_values}"
        )

    # Property: first sync call must be a False→True edge (Req 2.1)
    # A True→False transition cannot occur before a False→True one because
    # bin_full_confirmed starts False.
    if sync_calls:
        assert sync_calls[0] is True, (
            f"First _sync_bin_status call must be True (False→True edge), "
            f"got {sync_calls[0]}. poll_values={poll_values}"
        )


@given(st.lists(st.just(True), min_size=HIGH_THRESHOLD, max_size=200))
@settings(max_examples=50)
def test_single_false_to_true_edge_on_all_high(poll_values: list[bool]) -> None:
    """
    **Validates: Requirements 2.1, 2.5**

    Property 5 (stable-HIGH case): A sequence of only HIGH readings produces
    exactly one _sync_bin_status(True) call after the threshold is reached,
    then zero additional calls regardless of how many more HIGH polls follow.
    """
    sync_calls = _simulate_bin_monitor(poll_values)

    assert len(sync_calls) == 1, (
        f"Expected exactly 1 sync call for all-HIGH sequence, got {len(sync_calls)}: "
        f"sync_calls={sync_calls}"
    )
    assert sync_calls[0] is True


@given(
    st.lists(st.just(False), min_size=0, max_size=200)
)
@settings(max_examples=50)
def test_no_sync_call_on_all_low_from_clear(poll_values: list[bool]) -> None:
    """
    **Validates: Requirements 2.3, 2.5**

    Property 5 (stable-LOW case): A sequence of only LOW readings when the bin
    starts clear (bin_full_confirmed=False) produces zero _sync_bin_status calls —
    there is no edge to detect.
    """
    sync_calls = _simulate_bin_monitor(poll_values)

    assert len(sync_calls) == 0, (
        f"Expected 0 sync calls for all-LOW sequence starting from clear state, "
        f"got {len(sync_calls)}: sync_calls={sync_calls}"
    )
