# GPIO Pin assignments (BCM numbering) for Raspberry Pi 5
# Adjust these to match your actual wiring

PIN_BOTTLE_INSERTED = 17  # HIGH pulse when bottle is detected by sensor
PIN_BIN_FULL        = 27  # HIGH while bin-full sensor is triggered
PIN_DOOR_OPEN       = 22  # HIGH while door-open sensor is triggered

WS_HOST = "0.0.0.0"
WS_PORT = 8765

# Poll interval for level-triggered sensors (seconds)
POLL_INTERVAL = 0.2
