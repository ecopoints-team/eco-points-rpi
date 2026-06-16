from gpiozero import Button
from signal import pause

possible_pins = [
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27
]

print("--- WIRING DETECTIVE MODE ---")
print("Trigger your sensors now. I will tell you where they are.")
print("(Press Ctrl+C to stop)")
print("-" * 30)

def report_activity(device):
    print(f" >> SIGNAL DETECTED ON: GPIO {device.pin.number}")

# Listener for every single pin
detectors = []
for pin_num in possible_pins:
    try:
        sensor = Button(pin_num, pull_up=True)
        sensor.when_pressed = report_activity
        sensor.when_released = report_activity
        detectors.append(sensor)
    except Exception as e:
        print(f"Skipping GPIO {pin_num} (Busy or Error)")

pause()