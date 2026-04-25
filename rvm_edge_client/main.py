import time
import sys
import random
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
MACHINE_ID = os.getenv("MACHINE_ID", "RVM-MAIN-001")
LOCATION = os.getenv("LOCATION", "Institute of Technology")

# --- CONFIGURATION ---
PIN_DOOR_SENSOR = 26
PIN_STORAGE_LEVEL = 29
# PIN LIMIT SWITCH 1 = 24
# PIN LIMIT SWITCH 2 = 31
# PIN PWM = 11
# PIN DIRECTION = 12
# PIN InProgressIndicator = 15



class HardwareInterface:
    """
    Simulates the low-level hardware interactions.
    """

    def log(self, system, message):
        """Prints formatted logs like a real system terminal."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{system:<8}] : {message}")
        time.sleep(0.3)  # Artificial latency for realism

    def boot_sequence(self):
        print("\n" + "=" * 50)
        print("      ECO-POINTS EMBEDDED SYSTEM v2.4.1      ")
        print("=" * 50)
        self.log("KERNEL", "Initializing system...")
        time.sleep(0.5)
        self.log("GPIO", "Setting up pin modes...")
        self.log("DRIVER", "Loading Camera Module (OpenCV)...")
        self.log("DRIVER", "Calibrating Load Cells...")
        self.log("NET", "Connecting to cloud database... SUCCESS")
        self.log("SYS", "System Ready. Standing by.")
        print("-" * 50)

    def read_sensor_override(self, sensor_name, prompt):
        """
        Simulates reading a hardware sensor.

        """
        print(f"\n   >>> [DEBUG INTERRUPT] Reading {sensor_name}...")
        while True:
            val = input(f"   >>> SIGNAL SIMULATION: {prompt} (1=Yes/High, 0=No/Low): ").strip()
            if val == '1':
                return True
            elif val == '0':
                return False
            else:
                print("   >>> ERROR: Invalid Signal. Input 1 or 0.")

    def display_ui(self, text):
        """Simulates sending text to the LCD screen."""
        print(f"\n[LCD DISPLAY] >> \"{text}\"\n")

    def spin_motor(self, duration=1):
        self.log("MOTOR", "Actuator active...")
        time.sleep(duration)
        self.log("MOTOR", "Position reached.")


# --- MAIN LOGIC  ---
def run_ecopoints_firmware():
    hw = HardwareInterface()
    hw.boot_sequence()

    user_total_points = 0

    while True:
        # --- STATE: IDLE / WELCOME ---
        hw.log("SYS", "State: IDLE")

        # Check Storage Sensor
        hw.log("SENSOR", f"Reading PIN_{PIN_STORAGE_LEVEL} (Storage Level)...")
        #  Just a simulation to sensors. It should be automatic in the actual machine.
        is_full = hw.read_sensor_override("Storage Sensor", "Is the bin FULL?")

        if is_full:
            hw.display_ui("Sorry, machine is currently full. Please try again later.")
            hw.log("SYS", "Error: Capacity Reached. Entering sleep mode for 5s.")
            time.sleep(5)
            continue  # Restart loop

        hw.display_ui("Press Start Button")
        input("   >>> [BUTTON INPUT] Press ENTER to simulate Start Button click...")

        # --- STATE: QR SCANNING ---
        hw.display_ui("Showing QR Code...")
        hw.log("CAM", "Camera ON. Searching for QR pattern...")

        qr_flow_complete = False
        while not qr_flow_complete:
            # Simulate waiting for scan
            time.sleep(1)
            is_scanned = hw.read_sensor_override("Camera", "Did the user SCAN the QR?")

            if not is_scanned:
                hw.log("TIMER", "Timeout reached (120s).")
                hw.log("SYS", "Resetting session...")
                qr_flow_complete = "TIMEOUT"
                break

            hw.log("API", f"Verifying QR Token with server at {BACKEND_URL}...")
            try:
                # In real life, camera reads this. For now, simulate user input or hardcode.
                scanned_qr_data = input("   >>> [SCAN SIMULATION] Enter user ID (or press enter for dummy_user): ").strip()
                if not scanned_qr_data: scanned_qr_data = "dummy_user_123"
                
                response = requests.post(f"{BACKEND_URL}/api/verify_qr", json={
                    "qr_data": scanned_qr_data,
                    "machine_id": MACHINE_ID
                })
                
                if response.status_code == 200:
                    is_valid = True
                    user_data = response.json()
                    hw.log("API", f"User {user_data.get('name', 'Unknown')} authenticated.")
                else:
                    is_valid = False
            except requests.exceptions.RequestException as e:
                hw.log("API_ERROR", f"Could not connect to backend: {e}")
                is_valid = False

            if not is_valid:
                hw.display_ui("QR not recognized. Please try again.")
                hw.log("WARN", "Invalid Token detected.")
                # Loops back inside the QR loop
            else:
                hw.log("API", "Token Authenticated.")
                qr_flow_complete = True

        if qr_flow_complete == "TIMEOUT":
            continue

        # --- STATE: TRANSACTION START ---
        transacting = True

        while transacting:
            hw.display_ui("Please insert bottles in place")
            hw.log("MECH", "Unlocking Safety Door...")
            hw.log("MECH", "Door Unlocked.")

            # --- DOOR CHECK LOOP ---
            while True:
                # Simulating a magnetic reed switch on the door
                is_closed = hw.read_sensor_override("Door Sensor", "Is the door CLOSED?")
                if not is_closed:
                    hw.display_ui("Door Open. Please close the door to proceed.")
                    hw.log("WARN", f"GPIO_{PIN_DOOR_SENSOR} State: OPEN")
                else:
                    hw.log("INFO", f"GPIO_{PIN_DOOR_SENSOR} State: CLOSED")
                    hw.log("MECH", "Locking Safety Door...")
                    break

            # --- PLATFORM EMPTY CHECK ---
            hw.log("SCALE", "Taring scale...")
            is_empty = hw.read_sensor_override("Weight Scale", "Is the platform EMPTY (User put nothing in)?")

            if is_empty:
                hw.log("TIMER", "Activity Timeout. No object detected.")
                hw.log("SYS", "Resetting...")
                transacting = False
                break  # Goes back to main "Welcome" loop

            # --- VERIFICATION ---
            hw.log("PROC", "Verifying Objects...")
            hw.display_ui("Processing...")
            hw.spin_motor(duration=1.5)  # Simulate conveyor/scanner moving

            # --- VALIDITY CHECK LOOP ---
            # Loops back to verify if invalid
            bottles_valid = False
            while not bottles_valid:
                # Computer Vision simulation
                bottles_valid = hw.read_sensor_override("CV Model", "Are the bottles VALID (Plastic/Glass)?")

                if not bottles_valid:
                    hw.log("ERR", "Object Classification: INVALID/FOREIGN OBJECT")
                    hw.display_ui("Transaction Denied: Invalid Item Detected")
                    hw.display_ui("Please remove invalid item")

                    hw.log("MECH", "Unlocking door for removal...")
                    input("   >>> [USER ACTION] Press ENTER once you have removed the item...")
                    hw.log("MECH", "Door Locked. Retrying scan...")
                else:
                    hw.log("INFO", "Object Classification: PET BOTTLE (Accepted)")

            # --- CALCULATION ---
            points = 10
            user_total_points += points

            hw.log("DB", f"Updating User Session... +{points} pts")
            try:
                # Send the exact data the RecentActivity.jsx component expects
                response = requests.post(f"{BACKEND_URL}/api/add_points", json={
                    "qr_data": scanned_qr_data,
                    "points_added": points,
                    "bottles_added": 1,
                    "location": LOCATION,
                    "machine_id": MACHINE_ID,
                    "description": "Recycled Bottles",
                    "category": "PET Plastic"
                })
                if response.status_code == 200:
                    hw.log("DB", "Points successfully synced to the cloud.")
                else:
                    hw.log("DB", "Failed to sync points. Saving to local cache.")
            except Exception as e:
                hw.log("API_ERROR", "Server unreachable.")
            hw.display_ui(f"Transaction Successful + {points} Points!")
            hw.display_ui(f"Your Total Points : {user_total_points} pts")

            # --- TRANSACT ANOTHER? ---
            hw.log("SYS", "Waiting for user decision...")
            again = hw.read_sensor_override("Touchscreen", "Does user press 'Transact Another'?")

            if again:
                hw.log("SYS", "Looping transaction...")
                continue
            else:
                transacting = False

        # --- END OF SESSION ---
        if qr_flow_complete != "TIMEOUT":
            hw.display_ui(f"Your Total Points : {user_total_points} pts")
            hw.log("DB", "Committing session to database...")
            hw.log("SYS", "Session Finalized.")
            hw.display_ui("Thank you for using EcoPoints.")

            # Reset local variables
            user_total_points = 0
            hw.log("SYS", "Clearing cache...")
            time.sleep(2)


if __name__ == "__main__":
    try:
        run_ecopoints_firmware()
    except KeyboardInterrupt:
        print("\n[KERNEL PANIC] Force Shutdown initiated by user.")