import os
import sys

os.environ.setdefault("DISABLE_GPIO", "true")
os.environ.setdefault("MACHINE_ID", "TEST-001")
os.environ.setdefault("BACKEND_URL", "http://localhost:5000")
os.environ.setdefault("API_KEY", "test_key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings
from hypothesis import strategies as st
import main

# All 21 size tokens that verify_bottle() can return (Req 3.4)
ALL_SIZE_TOKENS = [
    "extra small", "xs", "small", "s", "medium", "m", "large", "l",
    "1000ml", "750ml", "551ml", "600ml", "550ml", "500ml",
    "351ml", "350ml", "330ml", "290ml", "289ml", "250ml", "125ml",
]


@given(st.sampled_from(ALL_SIZE_TOKENS))
@settings(max_examples=100)
def test_points_default_covers_all_tokens(token):
    """
    Property 7: Points config fallback completeness.
    Every size token has a non-zero int entry in POINTS_DEFAULT.

    **Validates: Requirements 3.3, 3.4**
    """
    assert token in main.POINTS_DEFAULT, f"Token '{token}' missing from POINTS_DEFAULT"
    assert isinstance(main.POINTS_DEFAULT[token], int), f"Token '{token}' value is not int"
    assert main.POINTS_DEFAULT[token] > 0, f"Token '{token}' has zero/negative points"


def test_all_21_tokens_covered():
    """Explicit check: all 21 known tokens are present and non-zero."""
    for token in ALL_SIZE_TOKENS:
        assert token in main.POINTS_DEFAULT, f"Missing: {token}"
        assert main.POINTS_DEFAULT[token] > 0, f"Zero points for: {token}"
