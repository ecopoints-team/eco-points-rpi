import time
import sys

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO library not found. Please run this script directly on the Raspberry Pi.")
    sys.exit(1)

# List of common GPIO pins (BCM numbering) to test
PINS_TO_TEST = [22, 27, 17, 18, 23, 24, 25, 5, 6, 12, 13, 16, 19, 20, 21, 26]

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    print("=" * 60)
    print("             RVM LIGHTS GPIO MAPPING TOOL             ")
    print("=" * 60)
    print("This script will toggle pins HIGH (3 seconds) and then LOW (1 second).")
    print("Watch the physical lights on your RVM to identify them.")
    print("Press Ctrl+C at any time to exit.\n")

    results = {}

    try:
        for pin in PINS_TO_TEST:
            print(f"\n--- Testing GPIO {pin} ---")
            
            # Setup pin as output
            GPIO.setup(pin, GPIO.OUT)
            
            # 1. Drive HIGH
            print(f"Setting GPIO {pin} to HIGH (ON if active-high)...")
            GPIO.output(pin, GPIO.HIGH)
            
            # Check point
            start_time = time.time()
            while time.time() - start_time < 3:
                time.sleep(0.1)
            
            # 2. Drive LOW
            print(f"Setting GPIO {pin} to LOW (OFF if active-high / ON if active-low)...")
            GPIO.output(pin, GPIO.LOW)
            time.sleep(1.0)
            
            # Prompt user
            try:
                ans = input(f"Did you see a light turn ON/OFF for GPIO {pin}? (y/n, Enter to skip): ").strip().lower()
                if ans == 'y':
                    desc = input("Describe which light/action occurred (e.g. green, orange, red, strobe): ").strip()
                    results[pin] = desc
                    print(f"Mapped: GPIO {pin} -> {desc}")
            except KeyboardInterrupt:
                raise
            except Exception:
                pass
                
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
    finally:
        print("\nCleaning up GPIO configuration...")
        GPIO.cleanup()
        
    print("\n" + "=" * 60)
    print("                     TESTING COMPLETE                     ")
    print("=" * 60)
    if results:
        print("Here is your mapped hardware configuration:")
        for pin, desc in results.items():
            print(f"  GPIO {pin:2d} -> {desc}")
    else:
        print("No lights were mapped.")
    print("=" * 60)

if __name__ == "__main__":
    main()
