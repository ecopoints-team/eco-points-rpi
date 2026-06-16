# 01_test_outputs.py
from gpiozero import LED
from time import sleep

# --- PIN CONFIGURATION ---
strobe_light = LED(17)  # Pin 11
progress_led = LED(11)  # Pin 23
power_led    = LED(5)   # Pin 29

print("--- TEST 1: OUTPUTS ---")

# 1. Power LED
print("1. Testing Power LED (Pin 29)...")
power_led.on()
sleep(1)
power_led.off()

# 2. Progress LED
print("2. Testing In-Progress LED (Pin 23)...")
progress_led.on()
sleep(1)
progress_led.off()

# 3. Strobe Light
print("3. Testing Strobe Light (Pin 11)...")
# Flashes 5 times quickly
strobe_light.blink(on_time=0.1, off_time=0.1, n=5)
sleep(1)

print("Output Test Complete.")