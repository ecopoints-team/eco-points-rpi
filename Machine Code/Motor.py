# 03_test_motor_90.py
from gpiozero import OutputDevice, Button
from time import sleep

STEPS_TO_MOVE = 1250
PULSE_DELAY = 0.001

# --- PIN CONFIGURATION ---
pul = OutputDevice(12)  # Pin 32
dir = OutputDevice(16)   # Pin 36
# limit = Button(27)      # Pin 13

print("Attempt to Move 90 deg")

dir.on()

for x in range(STEPS_TO_MOVE):
    pul.on()
    sleep(PULSE_DELAY)
    pul.off()
    sleep(PULSE_DELAY)

print("Finished")