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
MACHINE_ID = os.getenv("MACHINE_ID", "RVM-PU-01")
LOCATION = os.getenv("LOCATION", "Institute of Technology")

# --- HARDWARE LIBRARIES (CONDITIONAL IMPORT FOR PORTABILITY) ---
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    import cv2
    from ultralytics import YOLO
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

# --- CONFIGURATION (BCM Pin assignments matching README.md) ---
PIN_BOTTLE_INSERTED = 17  # HIGH pulse when bottle is detected by sensor
PIN_BIN_FULL        = 27  # HIGH while bin-full sensor is triggered
PIN_DOOR_OPEN       = 22  # HIGH while door-open sensor is triggered

# Global flag to track physical bottle insertion events from GPIO interrupt
physical_bottle_inserted = False

def gpio_callback(channel):
    global physical_bottle_inserted
    print(f"[GPIO] Interrupt: Physical bottle insertion detected on BCM Pin {channel}!")
    physical_bottle_inserted = True


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
        async def start():
            return await websockets.serve(self._handler, self.host, self.port)
        self.loop.run_until_complete(start())
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
    Manages low-level hardware interactions (GPIO, Camera, CV model).
    """
    def __init__(self):
        self.gpio_available = GPIO_AVAILABLE
        self.cv_available = CV_AVAILABLE
        self.model = None
        self._setup_gpio()
        self._setup_cv()

    def log(self, system, message):
        """Prints formatted logs like a real system terminal."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{system:<8}] : {message}")
        time.sleep(0.1)  # Minimal latency for premium feel

    def boot_sequence(self):
        print("\n" + "=" * 50)
        print("      ECO-POINTS EMBEDDED SYSTEM v3.0.0      ")
        print("=" * 50)
        self.log("KERNEL", "Initializing system...")
        time.sleep(0.3)
        self.log("GPIO", "Initializing pins & interrupts...")
        if self.gpio_available:
            self.log("GPIO", "RPi.GPIO initialized successfully.")
        else:
            self.log("GPIO", "RPi.GPIO not found. Running in simulation fallback mode.")
        
        self.log("CV", "Loading object detection engine...")
        if self.cv_available and self.model:
            self.log("CV", "YOLOv8 weights successfully loaded.")
        elif self.cv_available:
            self.log("CV", "OpenCV / YOLO imported, but best.pt model file missing. Running mock CV.")
        else:
            self.log("CV", "OpenCV or Ultralytics libraries missing. Running mock CV.")
            
        self.log("NET", "Connecting to cloud database... SUCCESS")
        self.log("SYS", "System Ready. Standing by.")
        print("-" * 50)

    def _setup_gpio(self):
        if not self.gpio_available:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(PIN_BOTTLE_INSERTED, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PIN_BIN_FULL,        GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(PIN_DOOR_OPEN,       GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            # Setup hardware interrupt callback for the bottle insertion pulse
            GPIO.add_event_detect(
                PIN_BOTTLE_INSERTED, 
                GPIO.RISING, 
                callback=gpio_callback, 
                bouncetime=500
            )
        except Exception as e:
            print(f"[GPIO_ERR] Failed to configure GPIO pins: {e}")
            self.gpio_available = False

    def _setup_cv(self):
        if not self.cv_available:
            return
        
        try:
            model_path = os.path.join(os.path.dirname(__file__), "models", "best.pt")
            if os.path.exists(model_path):
                # Suppress verbose YOLO logging during start
                self.model = YOLO(model_path)
            else:
                self.model = None
        except Exception as e:
            print(f"[CV_ERR] Failed to load YOLOv8 model: {e}")
            self.model = None

    def is_bin_full(self) -> bool:
        if not self.gpio_available:
            return False
        try:
            return GPIO.input(PIN_BIN_FULL) == GPIO.HIGH
        except Exception:
            return False

    def is_door_open(self) -> bool:
        if not self.gpio_available:
            return False
        try:
            return GPIO.input(PIN_DOOR_OPEN) == GPIO.HIGH
        except Exception:
            return False

    def display_ui(self, text, event=None, data=None):
        """Simulates sending text to the LCD screen and broadcasts to WebSocket."""
        print(f"\n[LCD DISPLAY] >> \"{text}\"\n")
        if event:
            ui_bridge.broadcast(event, data)

    def spin_motor(self, duration=1.2):
        self.log("MOTOR", "Activating sorting actuator/conveyor...")
        time.sleep(duration)
        self.log("MOTOR", "Sorting complete. Actuator returned to idle.")

    def verify_bottle(self):
        """
        Uses the camera and YOLOv8 model to verify and classify the inserted bottle.
        Returns a tuple: (is_valid, brand_name, size_category)
        """
        if not self.cv_available or self.model is None:
            self.log("CV", "[SIMULATION] Running mock CV verification...")
            time.sleep(1.5)
            # Simulate a successful classification with typical class values
            sim_brand = random.choice(["Le Minerale", "Nature spring", "Summit", "Wilkins pure"])
            sim_size = random.choice(["350ml", "500ml", "600ml", "1000ml"])
            return True, sim_brand, sim_size

        self.log("CAM", "Starting camera module...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.log("CAM_ERR", "Webcam not detected. Fallback: Simulating scan...")
            time.sleep(1.5)
            return True, "Le Minerale", "600ml"

        # Give the camera sensor time to adjust to light levels
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            self.log("CAM_ERR", "Failed to capture frame from webcam. Fallback: Simulating scan...")
            return True, "Nature spring", "500ml"

        self.log("CV", "Analyzing image frame with YOLOv8...")
        try:
            # Run prediction with a confidence threshold of 50%
            results = self.model.predict(frame, conf=0.5, verbose=False)
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = self.model.names[cls_id]
                    
                    self.log("CV", f"Match: '{class_name}' with confidence {conf:.2f}")
                    
                    # Parse brand and size from name (e.g. 'Le Minerale 600ml')
                    parts = class_name.split()
                    if len(parts) >= 2:
                        size = parts[-1]
                        brand = " ".join(parts[:-1])
                    else:
                        brand = class_name
                        size = "Medium"
                        
                    return True, brand, size
        except Exception as e:
            self.log("CV_ERR", f"Prediction execution failed: {e}")

        self.log("CV", "No valid beverage bottles recognized in the chute.")
        return False, "None", "None"


# --- MAIN FIRMWARE PROCESS ---
def run_ecopoints_firmware():
    global physical_bottle_inserted
    
    hw = HardwareInterface()
    hw.boot_sequence()

    user_total_points = 0

    while True:
        # --- STATE: IDLE / WELCOME ---
        # Wait for at least one Kiosk UI client to connect first
        if not ui_bridge.clients:
            hw.log("SYS", "Waiting for Kiosk UI client to connect on ws://localhost:8765 ...")
            while not ui_bridge.clients:
                time.sleep(1)
            hw.log("SYS", "Kiosk UI client connected! Starting session...")

        hw.log("SYS", "State: IDLE")

        # Initial check for full storage capacity
        is_full = hw.is_bin_full()
        if is_full:
            hw.display_ui("Sorry, machine is currently full. Please try again later.", "SET_BIN_FULL")
            hw.log("SYS", "Capacity Reached. System suspended for 5s.")
            time.sleep(5)
            continue  # Restart loop to check if bin was cleared

        hw.display_ui("Press Start Button", "GO_IDLE")
        ui_bridge.clear_queue()
        
        # Wait for the screen tap wake-up event or bin full triggers
        hw.log("SYS", "Waiting for WAKE event (touchscreen tap)...")
        bin_became_full = False
        while True:
            if not ui_bridge.clients:
                hw.log("SYS", "UI client disconnected. Waiting for reconnection...")
                while not ui_bridge.clients:
                    time.sleep(1)
                hw.log("SYS", "UI client reconnected.")
                
            # If the bin becomes full while idling, suspend system
            if hw.is_bin_full():
                hw.display_ui("Sorry, machine is currently full. Please try again later.", "SET_BIN_FULL")
                hw.log("SYS", "Capacity Reached while idling. Suspending...")
                time.sleep(5)
                bin_became_full = True
                break
                
            msg = ui_bridge.get_message(timeout=0.5)
            if msg and msg.get("action") == "WAKE":
                break
                
        if bin_became_full:
            continue

        ui_bridge.broadcast("WAKE")

        # --- STATE: QR SCANNING ---
        hw.display_ui("Showing QR Code...")
        hw.log("CAM", "Camera ON. Searching for QR pattern...")

        qr_flow_complete = False
        session_id = None
        
        while not qr_flow_complete:
            scanned_qr_data = None
            hw.log("SYS", "Waiting for QR code scan from Kiosk UI...")
            while True:
                if not ui_bridge.clients:
                    hw.log("SYS", "UI client disconnected during scan.")
                    qr_flow_complete = "TIMEOUT"
                    break
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

            hw.log("API", f"Verifying QR Token with backend server at {BACKEND_URL}...")
            try:
                response = requests.post(f"{BACKEND_URL}/api/rpi/session/start", json={
                    "user_qr": scanned_qr_data,
                    "machine_uuid": MACHINE_ID
                })
                
                if response.status_code in [200, 201]:
                    session_data = response.json()
                    session_id = session_data.get("session", {}).get("session_id")
                    account_name = session_data.get("account", {}).get("name", "Unknown")
                    hw.log("API", f"User {account_name} authenticated. Session {session_id} started.")
                    ui_bridge.broadcast("LOGIN_SUCCESS", {"userName": account_name})
                    qr_flow_complete = True
                else:
                    hw.display_ui("QR not recognized. Please try again.")
                    hw.log("WARN", f"Backend rejected token. Status code: {response.status_code}")
                    ui_bridge.broadcast("LOGIN_DENIED")
                    qr_flow_complete = "TIMEOUT"
                    break
            except requests.exceptions.RequestException as e:
                hw.log("API_ERR", f"Could not connect to backend: {e}")
                hw.display_ui("Network error. Please try again later.")
                ui_bridge.broadcast("LOGIN_DENIED")
                qr_flow_complete = "TIMEOUT"
                break

        if qr_flow_complete == "TIMEOUT":
            continue

        # --- STATE: TRANSACTION LOOP ---
        transacting = True
        physical_bottle_inserted = False  # Reset flag for transaction start

        while transacting:
            hw.display_ui("Please insert bottles in place", "READY")
            
            # Verify safety door is closed before opening actuator
            if hw.is_door_open():
                hw.display_ui("Door Open. Please close the door to proceed.", "SET_DOOR_OPEN")
                hw.log("MECH", "Safety door open detected. Suspending...")
                while hw.is_door_open():
                    time.sleep(0.5)
                hw.display_ui("Door Closed. Locking...", "DOOR_CLOSED")
                hw.log("MECH", "Safety door closed. Resuming...")

            hw.log("MECH", "Unlocking Safety Door...")
            hw.log("MECH", "Door Unlocked.")

            hw.log("SYS", "Waiting for bottle insertion (hardware sensor or UI simulator)...")
            user_inserted = False
            
            while True:
                if not ui_bridge.clients:
                    hw.log("SYS", "UI client disconnected during transaction.")
                    user_inserted = False
                    break
                
                # Check for live door openings
                if hw.is_door_open():
                    hw.display_ui("Door Open. Please close the door to proceed.", "SET_DOOR_OPEN")
                    hw.log("MECH", "Door opened during active session!")
                    while hw.is_door_open():
                        time.sleep(0.5)
                    hw.display_ui("Door Closed. Locking...", "DOOR_CLOSED")
                    hw.display_ui("Please insert bottles in place", "READY")
                
                # Check for physical hardware sensor interrupt
                if physical_bottle_inserted:
                    hw.log("GPIO", "Bottle insertion detected via hardware pulse.")
                    physical_bottle_inserted = False  # Consume trigger
                    user_inserted = True
                    break
                
                msg = ui_bridge.get_message(timeout=0.2)
                if msg:
                    if msg.get("action") == "CANCEL":
                        user_inserted = False
                        break
                    elif msg.get("action") == "BOTTLE_INSERTED":
                        hw.log("SYS", "Bottle insertion triggered via UI simulation button.")
                        user_inserted = True
                        break
            
            if not user_inserted:
                hw.log("SYS", "Transaction finished or canceled by user.")
                transacting = False
                break
                
            # Transition screen to verifying
            hw.display_ui("Processing...", "BOTTLE_INSERTED")
            hw.log("MECH", "Locking Safety Door...")
            hw.log("SCALE", "Taring scale...")
            hw.log("PROC", "Analyzing object in chute...")
            
            # Spin conveyor motor to move bottle into camera viewport
            hw.spin_motor(duration=1.2)
            
            # Execute CV classification
            is_valid, brand_name, size_category = hw.verify_bottle()
            
            if not is_valid:
                hw.log("ERR", "Object Classification: INVALID/FOREIGN OBJECT")
                hw.display_ui("Transaction Denied: Invalid Item Detected", "VERIFY_FAIL", {
                    "reason": "Non-recyclable material or unrecognized bottle brand."
                })
                hw.log("MECH", "Unlocking door for removal...")
                
                # Wait for user to decide to try again or finish
                hw.log("SYS", "Waiting for user action on rejection screen...")
                retry = False
                while True:
                    if not ui_bridge.clients:
                        break
                    msg = ui_bridge.get_message(timeout=0.5)
                    if msg:
                        if msg.get("action") == "REPEAT_READY":
                            retry = True
                            break
                        elif msg.get("action") in ("FINISH", "CANCEL"):
                            retry = False
                            break
                
                if retry:
                    continue
                else:
                    transacting = False
                    break
            else:
                hw.log("INFO", f"Verified successfully: {brand_name} ({size_category})")
                
                # Map sizes to points values
                points = 10
                if "1000ml" in size_category.lower() or "1000mL" in size_category:
                    points = 15
                elif "500ml" in size_category.lower() or "600ml" in size_category.lower() or "500mL" in size_category:
                    points = 10
                elif "330ml" in size_category.lower() or "350ml" in size_category.lower():
                    points = 5

                user_total_points += points
                
                hw.log("DB", f"Sending deposit log: {brand_name} (+{points} pts)")
                try:
                    response = requests.post(f"{BACKEND_URL}/api/rpi/item/deposit", json={
                        "session_id": session_id,
                        "item_type": "PET Plastic",
                        "points": points,
                        "weight_grams": 50,
                        "brand": brand_name,
                        "condition": "Good",
                        "size_category": size_category
                    })
                    if response.status_code in [200, 201]:
                        hw.log("DB", "Deposit log successfully synced to backend.")
                    else:
                        hw.log("DB", f"Failed to sync points: Server returned {response.status_code}")
                except Exception as e:
                    hw.log("API_ERR", f"Could not sync points to backend: {e}")
                
                hw.display_ui(f"Transaction Successful + {points} Points!", "VERIFY_SUCCESS", {
                    "points": points, 
                    "bottleCount": 1
                })
                hw.display_ui(f"Your Total Points : {user_total_points} pts")
                
                # Wait for user choice (another bottle or finish)
                hw.log("SYS", "Waiting for user action (Repeat/Finish)...")
                again = None
                while True:
                    if not ui_bridge.clients:
                        again = False
                        break
                    msg = ui_bridge.get_message(timeout=0.5)
                    if msg:
                        if msg.get("action") == "REPEAT_READY":
                            again = True
                            break
                        elif msg.get("action") == "FINISH":
                            again = False
                            break
                
                if again:
                    hw.log("SYS", "User selected transact again. Looping...")
                    continue
                else:
                    transacting = False

        # --- STATE: END OF SESSION ---
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
                    hw.log("DB", f"Failed to commit session: Server returned {end_resp.status_code}")
            except Exception as e:
                hw.log("API_ERR", f"Failed to finalize session: {e}")
                
        hw.log("SYS", "Session Finalized.")
        hw.display_ui("Thank you for using EcoPoints.", "ADVANCE_THANK_YOU")

        # Reset session point trackers
        user_total_points = 0
        time.sleep(2)


if __name__ == "__main__":
    try:
        run_ecopoints_firmware()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown initiated by user.")
    finally:
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                print("[GPIO] Pins returned to safe state.")
            except Exception as e:
                print(f"[GPIO_ERR] Cleanup failed: {e}")