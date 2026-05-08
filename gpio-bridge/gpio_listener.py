"""
gpio_listener.py — GPIO abstraction for Raspberry Pi 5
Wraps RPi.GPIO with clean methods for each sensor.
"""

import logging
from config import (
    PIN_BOTTLE_INSERTED,
    PIN_BIN_FULL,
    PIN_DOOR_OPEN,
    POLL_INTERVAL,
)

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    SIMULATION = False
except ImportError:
    logger.warning("RPi.GPIO not found — running in SIMULATION mode (all sensors LOW)")
    SIMULATION = True


class GPIOListener:
    def __init__(self):
        self.poll_interval = POLL_INTERVAL

    def setup(self):
        if SIMULATION:
            logger.info("Simulation mode: GPIO setup skipped")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_BOTTLE_INSERTED, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_BIN_FULL,        GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_DOOR_OPEN,       GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        logger.info("GPIO pins configured")

    def on_bottle_inserted(self, callback):
        """Register an edge-detect callback for the bottle-inserted pulse pin."""
        if SIMULATION:
            return
        GPIO.add_event_detect(
            PIN_BOTTLE_INSERTED,
            GPIO.RISING,
            callback=lambda _: callback(),
            bouncetime=500,  # ms debounce
        )

    def is_bin_full(self) -> bool:
        if SIMULATION:
            return False
        return GPIO.input(PIN_BIN_FULL) == GPIO.HIGH

    def is_door_open(self) -> bool:
        if SIMULATION:
            return False
        return GPIO.input(PIN_DOOR_OPEN) == GPIO.HIGH

    def cleanup(self):
        if not SIMULATION:
            GPIO.cleanup()
            logger.info("GPIO cleanup done")
