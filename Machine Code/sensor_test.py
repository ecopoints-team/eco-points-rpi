# 02_test_sensors.py
from gpiozero import Button, DigitalInputDevice
from time import sleep

# --- PIN CONFIGURATION ---
limit_switch   = Button(6)        # Pin 13
# door_sensor    = Button(22)        # Pin 15
# curtain_sensor = DigitalInputDevice(23, pull_up=True) # Pin 16

print("--- TEST 2: SENSORS ---")
print("Press Ctrl+C to stop.")

try:
    while True:
        # Check Status
        homing = "HIT" if limit_switch.is_pressed else "OPEN"
        # door   = "CLOSED" if door_sensor.is_pressed else "OPEN"
        # bin    = "FULL" if curtain_sensor.is_active else "EMPTY"
        
        # Print on one line
        print(f"Homing: {homing}")
            #   |  Door: {door}  |  Bin: {bin}   ", end="\r")
        sleep(0.1)

except KeyboardInterrupt:
    print("\nTest Stopped.")