import time
import sys
import random
from datetime import datetime
import os
import requests
import json
import asyncio
import threading
import websockets
import queue
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

# --- UI BRIDGE ---
class UIBridge:
    """Manages WebSocket communication with the Kiosk UI."""
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.queue = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_server, daemon=True)

    def start(self):
        self.thread.start()

    def _run_server(self):
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self._handler, self.host, self.port)
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    async def _handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.queue.put(data)
                except json.JSONDecodeError:
                    self.queue.put({"action": message})
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)

    def get_message(self, timeout=None):
        """Reads the next message from the queue with an optional timeout."""
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Discards all pending messages in the queue."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def broadcast(self, event_type, data=None):
        """Sends an event to all connected UI clients."""
        if not self.clients:
            return
        
        message = {"event": event_type}
        if data:
            message.update(data)
            
        payload = json.dumps(message)
        # Schedule the send on the event loop thread
        for client in self.clients:
            self.loop.call_soon_threadsafe(
                asyncio.run_coroutine_threadsafe, 
                client.send(payload), 
                self.loop
            )

ui_bridge = UIBridge()
ui_bridge.start()



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

    def display_ui(self, text, event=None, data=None):
        """Simulates sending text to the LCD screen and broadcasts to WebSocket."""
        print(f"\n[LCD DISPLAY] >> \"{text}\"\n")
        if event:
            ui_bridge.broadcast(event, data)

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
            hw.display_ui("Sorry, machine is currently full. Please try again later.", "SET_BIN_FULL")
            hw.log("SYS", "Error: Capacity Reached. Entering sleep mode for 5s.")
            time.sleep(5)
            continue  # Restart loop

        hw.display_ui("Press Start Button", "GO_IDLE")
        ui_bridge.clear_queue()
        if not ui_bridge.clients:
            input("   >>> [BUTTON INPUT] Press ENTER to simulate Start Button click...")
        else:
            hw.log("SYS", "Waiting for WAKE event (touchscreen tap)...")
            while True:
                msg = ui_bridge.get_message(timeout=0.5)
                if msg and msg.get("action") == "WAKE":
                    break
        ui_bridge.broadcast("WAKE")

        # --- STATE: QR SCANNING ---
        hw.display_ui("Showing QR Code...")
        hw.log("CAM", "Camera ON. Searching for QR pattern...")

        qr_flow_complete = False
        session_id = None
        while not qr_flow_complete:
            scanned_qr_data = None
            if not ui_bridge.clients:
                # Simulate waiting for scan
                time.sleep(1)
                is_scanned = hw.read_sensor_override("Camera", "Did the user SCAN the QR?")

                if not is_scanned:
                    hw.log("TIMER", "Timeout reached (120s).")
                    hw.log("SYS", "Resetting session...")
                    qr_flow_complete = "TIMEOUT"
                    break
                
                # Simulate user input
                scanned_qr_data = input("   >>> [SCAN SIMULATION] Enter user ID (or press enter for dummy_user): ").strip()
                if not scanned_qr_data: scanned_qr_data = "dummy_user_123"
            else:
                hw.log("SYS", "Waiting for QR code scan from Kiosk UI...")
                while True:
                    msg = ui_bridge.get_message(timeout=0.5)
                    if msg:
                        if msg.get("action") == "CANCEL":
                            qr_flow_complete = "TIMEOUT"
                            break
                        elif msg.get("action") == "QR_SCANNED":
                            scanned_qr_data = msg.get("qr_data")
                            break
                if qr_flow_complete == "TIMEOUT" or not scanned_qr_data:
                    break

            hw.log("API", f"Verifying QR Token with server at {BACKEND_URL}...")
            try:
                response = requests.post(f"{BACKEND_URL}/api/rpi/session/start", json={
                    "user_qr": scanned_qr_data,
                    "machine_uuid": MACHINE_ID
                })
                
                if response.status_code in [200, 201]:
                    is_valid = True
                    session_data = response.json()
                    session_id = session_data.get("session", {}).get("session_id")
                    account_name = session_data.get("account", {}).get("name", "Unknown")
                    hw.log("API", f"User {account_name} authenticated. Session {session_id} started.")
                    ui_bridge.broadcast("LOGIN_SUCCESS", {"userName": account_name})
                else:
                    is_valid = False
                    ui_bridge.broadcast("LOGIN_DENIED")
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
            hw.display_ui("Please insert bottles in place", "READY")
            hw.log("MECH", "Unlocking Safety Door...")
            hw.log("MECH", "Door Unlocked.")

            # --- DOOR CHECK LOOP ---
            while True:
                # Simulating a magnetic reed switch on the door
                is_closed = hw.read_sensor_override("Door Sensor", "Is the door CLOSED?")
                if not is_closed:
                    hw.display_ui("Door Open. Please close the door to proceed.", "SET_DOOR_OPEN")
                    hw.log("WARN", f"GPIO_{PIN_DOOR_SENSOR} State: OPEN")
                else:
                    hw.log("INFO", f"GPIO_{PIN_DOOR_SENSOR} State: CLOSED")
                    hw.display_ui("Door Closed. Locking...", "DOOR_CLOSED")
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
            hw.display_ui("Processing...", "BOTTLE_INSERTED")
            hw.spin_motor(duration=1.5)  # Simulate conveyor/scanner moving

            # --- VALIDITY CHECK LOOP ---
            # Loops back to verify if invalid
            bottles_valid = False
            while not bottles_valid:
                # Computer Vision simulation
                bottles_valid = hw.read_sensor_override("CV Model", "Are the bottles VALID (Plastic/Glass)?")

                if not bottles_valid:
                    hw.log("ERR", "Object Classification: INVALID/FOREIGN OBJECT")
                    hw.display_ui("Transaction Denied: Invalid Item Detected", "VERIFY_FAIL", {"reason": "Non-recyclable material detected."})
                    hw.display_ui("Please remove invalid item")

                    hw.log("MECH", "Unlocking door for removal...")
                    if not ui_bridge.clients:
                        input("   >>> [USER ACTION] Press ENTER once you have removed the item...")
                    else:
                        hw.log("SYS", "Waiting for user action on Kiosk UI...")
                        user_wants_retry = None
                        while True:
                            msg = ui_bridge.get_message(timeout=0.5)
                            if msg:
                                if msg.get("action") == "REPEAT_READY":
                                    user_wants_retry = True
                                    break
                                elif msg.get("action") == "FINISH":
                                    user_wants_retry = False
                                    break
                        if not user_wants_retry:
                            transacting = False
                            break
                    hw.log("MECH", "Door Locked. Retrying scan...")
                else:
                    hw.log("INFO", "Object Classification: PET BOTTLE (Accepted)")

            # --- CALCULATION ---
            points = 10
            user_total_points += points

            hw.log("DB", f"Updating User Session... +{points} pts")
            try:
                # Send the exact data the RecentActivity.jsx component expects
                response = requests.post(f"{BACKEND_URL}/api/rpi/item/deposit", json={
                    "session_id": session_id,
                    "item_type": "PET Plastic",
                    "points": points,
                    "weight_grams": 50,
                    "brand": "Unknown",
                    "condition": "Good",
                    "size_category": "Medium"
                })
                if response.status_code in [200, 201]:
                    hw.log("DB", "Points successfully synced to the cloud.")
                else:
                    hw.log("DB", "Failed to sync points. Saving to local cache.")
            except Exception as e:
                hw.log("API_ERROR", "Server unreachable.")
            hw.display_ui(f"Transaction Successful + {points} Points!", "VERIFY_SUCCESS", {"points": points, "bottleCount": 1})
            hw.display_ui(f"Your Total Points : {user_total_points} pts")

            # --- TRANSACT ANOTHER? ---
            hw.log("SYS", "Waiting for user decision...")
            if not ui_bridge.clients:
                again = hw.read_sensor_override("Touchscreen", "Does user press 'Transact Another'?")
            else:
                hw.log("SYS", "Waiting for user selection on Kiosk UI...")
                again = None
                while True:
                    msg = ui_bridge.get_message(timeout=0.5)
                    if msg:
                        if msg.get("action") == "REPEAT_READY":
                            again = True
                            break
                        elif msg.get("action") == "FINISH":
                            again = False
                            break

            if again:
                hw.log("SYS", "Looping transaction...")
                continue
            else:
                transacting = False

        # --- END OF SESSION ---
        if qr_flow_complete != "TIMEOUT":
            hw.display_ui(f"Your Total Points : {user_total_points} pts")
            hw.log("DB", "Committing session to database...")
            if session_id:
                try:
                    end_resp = requests.post(f"{BACKEND_URL}/api/rpi/session/end", json={
                        "session_id": session_id,
                        "machine_uuid": MACHINE_ID
                    })
                    if end_resp.status_code in [200, 201]:
                        hw.log("DB", "Session successfully committed.")
                    else:
                        hw.log("DB", f"Failed to commit session. Server returned {end_resp.status_code}")
                except Exception as e:
                    hw.log("API_ERROR", f"Failed to end session: {e}")
            hw.log("SYS", "Session Finalized.")
            hw.display_ui("Thank you for using EcoPoints.", "ADVANCE_THANK_YOU")

            # Reset local variables
            user_total_points = 0
            hw.log("SYS", "Clearing cache...")
            time.sleep(2)


if __name__ == "__main__":
    try:
        run_ecopoints_firmware()
    except KeyboardInterrupt:
        print("\n[KERNEL PANIC] Force Shutdown initiated by user.")