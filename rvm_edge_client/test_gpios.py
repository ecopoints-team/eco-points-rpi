import RPi.GPIO as GPIO
import time
import sys

# Pin assignments
PIN_MOTOR_PULSE  = 12
PIN_MOTOR_DIR    = 16
PIN_MOTOR_ENABLE = 17
PIN_MOTOR_HOME   = 6
PIN_STROBE       = 22
PIN_BIN_FULL     = 5
PIN_DOOR_OPEN    = 11
PIN_FAULT_LED    = 27
PIN_IN_PROGRESS  = 26

def setup_gpios():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Setup Inputs
    GPIO.setup(PIN_MOTOR_HOME, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_BIN_FULL,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Try PUD_UP for the door sensor in case the physical switch is wired to Ground (NC/NO to GND)
    GPIO.setup(PIN_DOOR_OPEN,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Setup Outputs (default HIGH / OFF)
    GPIO.setup(PIN_MOTOR_ENABLE, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(PIN_MOTOR_PULSE,  GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_MOTOR_DIR,    GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_STROBE,       GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(PIN_FAULT_LED,    GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(PIN_IN_PROGRESS,  GPIO.OUT, initial=GPIO.HIGH)

def test_inputs_loop():
    print("\n--- Live Input Monitoring ---")
    print("Press Ctrl+C to stop input monitoring and return to the main menu.\n")
    
    last_states = {}
    try:
        while True:
            # Read pins
            home_val = GPIO.input(PIN_MOTOR_HOME)
            bin_val = GPIO.input(PIN_BIN_FULL)
            door_val = GPIO.input(PIN_DOOR_OPEN)
            
            states = {
                "Homing Sensor (Pin 6)": "LOW / TRIGGERED (GND)" if home_val == GPIO.LOW else "HIGH / UNTRIGGERED",
                "Bin Full Sensor (Pin 5)": "HIGH / BLOCKED (FULL)" if bin_val == GPIO.HIGH else "LOW / CLEAR",
                "Door Open Sensor (Pin 11)": "LOW / TRIGGERED" if door_val == GPIO.LOW else "HIGH / UNTRIGGERED"
            }
            
            # Print only on state changes to avoid flooding the screen
            changed = False
            for k, v in states.items():
                if last_states.get(k) != v:
                    print(f"[STATE CHANGE] {k} -> {v}")
                    changed = True
            
            if changed:
                last_states = states
                
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nInput monitoring stopped.")

def toggle_output(pin, pin_name):
    current = GPIO.input(pin)
    new_state = GPIO.LOW if current == GPIO.HIGH else GPIO.HIGH
    GPIO.output(pin, new_state)
    state_str = "ON / LOW" if new_state == GPIO.LOW else "OFF / HIGH"
    print(f"\nToggled {pin_name} (Pin {pin}) to {state_str}")

def pulse_motor():
    print("\n--- Pulse Motor Test ---")
    steps = input("Enter number of steps to pulse (default 200): ")
    try:
        steps = int(steps) if steps.strip() else 200
    except ValueError:
        print("Invalid number. Using 200.")
        steps = 200

    direction = input("Enter direction (1 = forward/HIGH, 0 = backward/LOW, default 1): ")
    dir_val = GPIO.HIGH if direction != "0" else GPIO.LOW

    print(f"Enabling motor driver, setting direction, and sending {steps} pulses...")
    try:
        # Enable motor driver (active-LOW)
        GPIO.output(PIN_MOTOR_ENABLE, GPIO.LOW)
        GPIO.output(PIN_MOTOR_DIR, dir_val)
        time.sleep(0.1)

        for i in range(steps):
            GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
            time.sleep(0.002)
            GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
            time.sleep(0.002)

        print("Pulses sent successfully.")
    except Exception as e:
        print(f"Error pulsing motor: {e}")
    finally:
        # Disable motor driver
        GPIO.output(PIN_MOTOR_ENABLE, GPIO.HIGH)
        print("Motor driver disabled.")

def full_cycle_test():
    print("\n--- Full Dispense Cycle Test ---")
    steps = input("Enter number of steps to drop (default 1250): ")
    try:
        steps = int(steps) if steps.strip() else 1250
    except ValueError:
        steps = 1250

    try:
        GPIO.output(PIN_MOTOR_ENABLE, GPIO.LOW)
        
        print("0. INITIAL SETUP: Raising platform (DIR=HIGH) to ensure it starts in default raised position...")
        GPIO.output(PIN_MOTOR_DIR, GPIO.HIGH)
        time.sleep(0.1)
        for i in range(steps):
            GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
            time.sleep(0.002)
            GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
            time.sleep(0.002)
        print("Platform is now raised. Waiting 2 seconds before dropping...")
        time.sleep(2)

        print(f"1. Enabling motor driver and dropping platform ({steps} steps, DIR=LOW)...")
        GPIO.output(PIN_MOTOR_DIR, GPIO.LOW)
        time.sleep(0.1)

        for i in range(steps):
            GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
            time.sleep(0.002)
            GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
            time.sleep(0.002)

        print("Platform dropped. Waiting 1 second...")
        time.sleep(1)

        print("2. Raising platform (DIR=HIGH) until Homing Sensor (Pin 6) triggers...")
        GPIO.output(PIN_MOTOR_DIR, GPIO.HIGH)
        time.sleep(0.1)
        
        timeout = time.time() + 10.0
        while GPIO.input(PIN_MOTOR_HOME) != GPIO.LOW and time.time() < timeout:
            GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
            time.sleep(0.002)
            GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
            time.sleep(0.002)
            
        if time.time() >= timeout:
            print("WARNING: Homing timeout reached! Sensor was never triggered.")
        else:
            print("Homing complete! Platform is raised.")
            
    except Exception as e:
        print(f"Error during cycle test: {e}")
    finally:
        GPIO.output(PIN_MOTOR_ENABLE, GPIO.HIGH)
        print("Motor driver disabled.")

def main():
    try:
        setup_gpios()
    except Exception as e:
        print(f"Failed to initialize GPIO pins. Are you running as root (sudo)? Error: {e}")
        sys.exit(1)

    print("=" * 60)
    print("           ECOPOINTS RVM GPIO TESTER SCRIPT            ")
    print("=" * 60)
    
    while True:
        print("\n[ SELECT AN OPTION ]")
        print("1) Live Input Monitoring (Pin 5, 6, 11)")
        print("2) Toggle Red LED (Pin 27 - Active LOW)")
        print("3) Toggle Orange LED (Pin 26 - Active LOW)")
        print("4) Toggle Strobe Light (Pin 22 - Active LOW)")
        print("5) Raw Stepper Motor Pulse Test (Manual Steps & Direction)")
        print("6) Full Dispense Cycle Test (Drop then Home/Raise automatically)")
        print("q) Quit and Clean Up GPIOs")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == '1':
            test_inputs_loop()
        elif choice == '2':
            toggle_output(PIN_FAULT_LED, "Red LED")
        elif choice == '3':
            toggle_output(PIN_IN_PROGRESS, "Orange LED")
        elif choice == '4':
            toggle_output(PIN_STROBE, "Strobe Light")
        elif choice == '5':
            pulse_motor()
        elif choice == '6':
            full_cycle_test()
        elif choice == 'q':
            print("\nCleaning up GPIO pins and exiting...")
            GPIO.cleanup()
            break
        else:
            print("\nInvalid choice. Try again.")

if __name__ == "__main__":
    main()
