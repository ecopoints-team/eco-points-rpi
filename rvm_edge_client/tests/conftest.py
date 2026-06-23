"""
conftest.py — test isolation helpers for rvm_edge_client tests.

Any test that starts a run_ecopoints_firmware() daemon thread will leave it
running after the test completes (daemon threads are not automatically joined).
If a subsequent test patches main.ui_bridge, the leftover daemon wakes up,
competes for injected messages, and causes flaky failures.

This fixture solves the problem by:
  1. Before each test: clear _firmware_stop_event so fresh firmware threads
     are not immediately stopped.
  2. After each test:  set _firmware_stop_event so any leftover firmware
     daemon sees the stop flag on its next outer-loop iteration and exits
     cleanly within ≤1 s (the sleep(1) in the client-wait inner loop).

IMPORTANT: This conftest sets test env vars at module level so they are in
place BEFORE any test module imports main.  This ensures main.MACHINE_ID etc.
are bound to test values, not the production .env values.
"""
import os
import sys
import time

# ---------------------------------------------------------------------------
# Set test env vars at MODULE LEVEL so they are in place before any test
# module triggers the first import of main (which calls load_dotenv()).
# load_dotenv() does NOT override existing os.environ values by default, so
# setting them here guarantees the test values win.
# ---------------------------------------------------------------------------
os.environ["DISABLE_GPIO"] = "true"
os.environ["MACHINE_ID"] = "TEST-001"
os.environ["API_KEY"] = "test_key"
# Do NOT set BACKEND_URL here — tests set their own values and we don't want
# a single override to break tests that expect specific base URLs.

import pytest

# Ensure main is importable from the tests directory without importing it here
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def reset_firmware_stop_event():
    """
    Auto-use fixture: clears _firmware_stop_event before every test, then
    sets it after every test so that any lingering firmware daemon threads
    exit cleanly before the next test begins.
    """
    # Lazy import so the module is resolved after all test collection is done
    import main as _main

    # --- Setup: clear so new firmware threads run normally ---
    _main._firmware_stop_event.clear()

    yield

    # --- Teardown: signal all running firmware loops to stop ---
    _main._firmware_stop_event.set()

    # Give daemon threads one full poll cycle (1 s) to notice the event
    # and exit, preventing them from stealing messages in the next test.
    time.sleep(1.1)

    # Clear again so the event is in a known state for the next test's
    # setup phase (belt-and-suspenders alongside the setup clear above).
    _main._firmware_stop_event.clear()
