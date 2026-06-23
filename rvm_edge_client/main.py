import time
import sys
import random
import logging
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
API_KEY = os.getenv("API_KEY", "")
SHOW_CV_WINDOW = os.getenv("CLI_MODE", "false").lower() == "true"
UHUBCTL_LOCATIONS = os.getenv("UHUBCTL_LOCATIONS", "")
UHUBCTL_PORT = os.getenv("UHUBCTL_PORT", "")

# ---------------------------------------------------------------------------
# Test-isolation stop flag
# ---------------------------------------------------------------------------
# Tests can set this event to break the run_ecopoints_firmware() infinite loop
# cleanly.  In production it is never set.
_firmware_stop_event = threading.Event()

# --- HARDWARE LIBRARIES (CONDITIONAL IMPORT FOR PORTABILITY) ---
try:
    import RPi.GPIO as GPIO
    # Allow overriding GPIO availability via .env if hardware is missing
    GPIO_AVAILABLE = os.getenv("DISABLE_GPIO", "false").lower() != "true"
except ImportError:
    GPIO_AVAILABLE = False

try:
    import cv2
    from ultralytics import YOLO
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

# --- CONFIGURATION (BCM Pin assignments matching README.md) ---
PIN_MOTOR_PULSE  = 12  # BCM 12 — step pulse
PIN_MOTOR_DIR    = 16  # BCM 16 — direction
PIN_MOTOR_ENABLE = 17  # BCM 17 — driver enable, active-LOW
PIN_MOTOR_HOME   = 6   # BCM 6  — homing sensor SW2
PIN_IN_PROGRESS  = 26  # BCM 26 — In Progress indicator, active-LOW
PIN_STROBE       = 22  # BCM 22 — Strobe light
PIN_BIN_FULL     = 5   # HIGH while bin-full sensor is triggered (BCM 5 / Pin 29)
PIN_DOOR_OPEN    = 11  # HIGH while door-open sensor is triggered (BCM 11 / Pin 23)

# --- POINTS CONFIGURATION ---
# Fallback points lookup used when the backend config fetch fails (Req 3.3, 3.4).
# Covers every size token that verify_bottle() can return.
POINTS_DEFAULT: dict[str, int] = {
    "extra small": 3, "xs": 3,
    "small": 5, "s": 5,
    "medium": 8, "m": 8,
    "large": 10, "l": 10,
    "1000ml": 10, "750ml": 10, "551ml": 10,
    "600ml": 8, "550ml": 8, "500ml": 8, "351ml": 8,
    "350ml": 5, "330ml": 5, "290ml": 5,
    "289ml": 3, "250ml": 3, "125ml": 3,
}


def fetch_points_config(
    backend_url: str,
    org_id: int,
    api_key: str,
    fallback: dict[str, int],
) -> dict[str, int]:
    """
    GET /api/rpi/config/points/<org_id> with a 10 s timeout.

    Returns response["config"] dict on HTTP 200 + "config" key present.
    Returns fallback on any error (network, timeout, non-200, missing key).
    Logs a warning on failure.
    """
    try:
        response = requests.get(
            f"{backend_url}/api/rpi/config/points/{org_id}",
            headers={"X-API-Key": api_key},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if "config" in data:
                return data["config"]
            print(f"[{__import__('datetime').datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [NET     ] : Points config response missing 'config' key. Using defaults.")
        else:
            print(f"[{__import__('datetime').datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [NET     ] : Points config fetch failed: HTTP {response.status_code}. Using defaults.")
    except Exception as e:
        print(f"[{__import__('datetime').datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [NET     ] : Points config fetch failed: {e}. Using defaults.")
    return fallback

# Light Indicators
PIN_FAULT_LED    = 27  # Red LED (BCM 27) — active-LOW (LOW=ON, HIGH=OFF)
# Note: The green LED is a hardwired power indicator (always ON when Pi has power).
#       It is NOT connected to any GPIO pin and cannot be software-controlled.

# Global flag to track physical bottle insertion events (via homing sensor / camera)
physical_bottle_inserted = False


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
            return await websockets.serve(self._handler, self.host, self.port, reuse_address=True, reuse_port=(os.name != 'nt'))
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
        self.picamera2_available = PICAMERA2_AVAILABLE
        self.model = None
        self._bin_full_confirmed = False
        self._setup_gpio()
        self._setup_cv()
        self._start_bin_monitor()

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
            self.log("CV", "YOLOv11 weights successfully loaded.")
        elif self.cv_available:
            self.log("CV", "OpenCV / YOLO imported, but best.pt model file missing. Running mock CV.")
        else:
            self.log("CV", "OpenCV or Ultralytics libraries missing. Running mock CV.")

        if self.picamera2_available:
            self.log("CAM", "picamera2 (libcamera) detected. Pi CSI camera will be used.")
        else:
            self.log("CAM", "picamera2 not found. Falling back to cv2.VideoCapture(0) (USB webcam).")
            
        self.log("NET", "Connecting to cloud database... SUCCESS")
        
        # Ensure QR scanner is OFF during idle
        self.set_scanner_power(False)

        self.log("SYS", "System Ready. Standing by.")
        print("-" * 50)

    def _setup_gpio(self):
        if not self.gpio_available:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)

            # Motor outputs — safe initial states (Req 5.2, 5.6)
            GPIO.setup(PIN_MOTOR_ENABLE, GPIO.OUT, initial=GPIO.HIGH)  # driver disabled (active-LOW)
            GPIO.setup(PIN_MOTOR_PULSE,  GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_MOTOR_DIR,    GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_IN_PROGRESS,  GPIO.OUT, initial=GPIO.HIGH)  # indicator off (active-LOW)
            GPIO.setup(PIN_STROBE,       GPIO.OUT, initial=GPIO.HIGH)  # strobe off (assuming active-LOW like others)

            # Homing sensor — input with pull-up (LOW = home position reached)
            GPIO.setup(PIN_MOTOR_HOME,   GPIO.IN,  pull_up_down=GPIO.PUD_UP)

            # Existing sensor/indicator pins
            GPIO.setup(PIN_BIN_FULL,     GPIO.IN,  pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_DOOR_OPEN,    GPIO.IN,  pull_up_down=GPIO.PUD_DOWN)

            # Red Fault LED is wired ACTIVE-LOW (cathode → GPIO 27, anode → 3.3V).
            # HIGH = LED OFF, LOW = LED ON. Initial state: HIGH (OFF).
            GPIO.setup(PIN_FAULT_LED,    GPIO.OUT, initial=GPIO.HIGH)
        except Exception as e:
            print(f"[GPIO_ERR] Failed to configure GPIO pins: {e}")
            self.gpio_available = False

    def shutdown_gpio(self):
        """Drive motor/indicator pins to safe states then release all GPIO resources."""
        if not self.gpio_available:
            return
        try:
            GPIO.output(PIN_MOTOR_ENABLE, GPIO.HIGH)  # disable driver (Req 5.7)
            GPIO.output(PIN_IN_PROGRESS,  GPIO.HIGH)  # indicator off (Req 5.7)
            GPIO.output(PIN_STROBE,       GPIO.HIGH)  # strobe off (active-LOW)
            # Drive Fault LED HIGH (OFF) before cleanup reverts it to floating INPUT mode.
            GPIO.output(PIN_FAULT_LED,    GPIO.HIGH)
        except Exception:
            pass
        GPIO.cleanup()

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
            print(f"[CV_ERR] Failed to load YOLOv11 model: {e}")
            self.model = None

    def _sync_bin_status(self, full: bool) -> None:
        """Fire-and-forget POST to /api/rpi/machine/status. Runs in a daemon thread (Req 2.6)."""
        def _worker():
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/api/rpi/machine/status",
                    headers={"X-API-Key": API_KEY},
                    json={"machineUuid": MACHINE_ID, "isCapacityFull": full},
                    timeout=10,
                )
                if resp.status_code not in (200, 201):
                    self.log("NET_WARN", f"machine/status returned {resp.status_code} (isCapacityFull={full})")
            except Exception as exc:
                self.log("NET_WARN", f"machine/status POST failed: {exc}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _start_bin_monitor(self):
        if self.gpio_available:
            t = threading.Thread(target=self._monitor_bin_full, daemon=True)
            t.start()

    def _monitor_bin_full(self):
        # Continuous background scan of the curtain/bin-full sensor
        consecutive_blocks = 0
        consecutive_clears = 0
        required_high_time = 5.0  # seconds of continuous block to declare full
        required_low_time = 0.5   # seconds of continuous clear to declare normal
        poll_interval = 0.1       # scan every 100ms
        
        high_threshold = int(required_high_time / poll_interval) # 50
        low_threshold = int(required_low_time / poll_interval)   # 5
        
        while True:
            try:
                # NC NPN Sensor under Pull-Up:
                # HIGH (1) = blocked (sensor floats, pull-up drives it HIGH) → bin FULL
                # LOW  (0) = clear  (sensor conducts to GND)                 → bin CLEAR
                if GPIO.input(PIN_BIN_FULL) == GPIO.HIGH:
                    consecutive_blocks += 1
                    consecutive_clears = 0
                    if consecutive_blocks >= high_threshold:
                        if not self._bin_full_confirmed:
                            # False → True edge transition (Req 2.1, 2.2)
                            self.log("GPIO", "Curtain sensor continuously blocked. Bin marked FULL.")
                            self._bin_full_confirmed = True
                            self._sync_bin_status(True)
                            ui_bridge.broadcast("SET_BIN_FULL")
                        
                        # Stable Red LED: LOW = ON (active-LOW)
                        GPIO.output(PIN_FAULT_LED, GPIO.LOW)
                else:
                    consecutive_clears += 1
                    consecutive_blocks = 0
                    if consecutive_clears >= low_threshold:
                        if self._bin_full_confirmed:
                            # True → False edge transition (Req 2.3, 2.4)
                            self.log("GPIO", "Curtain sensor cleared. Bin marked NORMAL.")
                            self._bin_full_confirmed = False
                            self._sync_bin_status(False)
                            ui_bridge.broadcast("CLEAR_BIN_FULL")
                        
                        # Turn OFF Red LED: HIGH = OFF (active-LOW)
                        GPIO.output(PIN_FAULT_LED, GPIO.HIGH)
            except Exception as e:
                pass
            time.sleep(poll_interval)

    def is_bin_full(self) -> bool:
        if not self.gpio_available:
            return False
        return self._bin_full_confirmed

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

    # Note: set_ready_led() removed — the green LED is a hardwired power indicator
    # (always ON when the Pi has power) and is not connected to any GPIO pin.

    def set_scanner_power(self, enable: bool):
        """Uses uhubctl to toggle USB port power for the QR Scanner."""
        if not self.gpio_available: # Only do this on the real Pi
            return
        state = "1" if enable else "0"
        action = "Activating" if enable else "Deactivating"
        self.log("USB", f"{action} QR Scanner Power (via uhubctl)...")
        try:
            if UHUBCTL_LOCATIONS:
                # Support multiple comma-separated hub locations (e.g. 3,4 on Pi 5)
                locations = [loc.strip() for loc in UHUBCTL_LOCATIONS.split(",") if loc.strip()]
                for loc in locations:
                    port_arg = f"-p {UHUBCTL_PORT} " if UHUBCTL_PORT else ""
                    cmd = f"sudo uhubctl -l {loc} {port_arg}-a {state}"
                    ret = os.system(f"{cmd} >/dev/null 2>&1")
                    if ret != 0:
                        self.log("USB_WARN", f"Command '{cmd}' failed with exit code {ret}.")
            else:
                # Fallback to default behavior
                cmd = f"sudo uhubctl -a {state}"
                ret = os.system(f"{cmd} >/dev/null 2>&1")
                if ret != 0:
                    self.log("USB_WARN", f"Command '{cmd}' failed with exit code {ret}.")
        except Exception as e:
            self.log("USB_ERR", f"Failed to run uhubctl: {e}")

    def spin_motor(self) -> None:
        """
        Drives stepper motor to open dispenser, waits, then homes it.
        Sets DIR HIGH (forward), pulses for MOTOR_OPEN_STEPS.
        Then sets DIR LOW (backward), pulses until homing sensor triggers.
        """
        # Load steps from environment to allow easy tuning without code changes (default: 1000, which is safer than 1250)
        steps = int(os.getenv("MOTOR_OPEN_STEPS", "1000"))
        
        self.log("MOTOR", f"Activating sorting actuator/conveyor ({steps} steps)...")
        if not self.gpio_available:
            time.sleep(1.2)
            self.log("MOTOR", "[SIMULATION] Sorting complete.")
            return

        try:
            # Enable motor (active-LOW)
            GPIO.output(PIN_MOTOR_ENABLE, GPIO.LOW)
            
            # Open Sequence
            self.log("MOTOR", "Opening dispenser...")
            GPIO.output(PIN_MOTOR_DIR, GPIO.HIGH)
            for _ in range(steps):
                GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
                time.sleep(0.001)
                GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
                time.sleep(0.001)
            
            time.sleep(0.5) # Wait for bottle to drop
            
            # Close Sequence (Home)
            self.log("MOTOR", "Homing dispenser...")
            GPIO.output(PIN_MOTOR_DIR, GPIO.LOW)
            
            timeout = time.time() + 10.0
            # Assuming home sensor is pulled up and shorts to ground (LOW) when closed
            while GPIO.input(PIN_MOTOR_HOME) != GPIO.LOW and time.time() < timeout:
                GPIO.output(PIN_MOTOR_PULSE, GPIO.HIGH)
                time.sleep(0.001)
                GPIO.output(PIN_MOTOR_PULSE, GPIO.LOW)
                time.sleep(0.001)
                
            self.log("MOTOR", "Sorting complete. Actuator returned to idle.")
        except Exception as e:
            self.log("MOTOR_ERR", f"GPIO error during spin_motor: {e}")
        finally:
            # Disable motor
            GPIO.output(PIN_MOTOR_ENABLE, GPIO.HIGH)

    def _open_camera(self):
        """
        Opens the best available camera source.
        Returns an object with a .read() method (numpy array) and a .release() method.
        Uses picamera2 (Pi CSI) when available, otherwise cv2.VideoCapture(0) (USB webcam).
        """
        if self.picamera2_available:
            try:
                cam = Picamera2()
                config = cam.create_preview_configuration(
                    main={"format": "RGB888", "size": (640, 480)}
                )
                cam.configure(config)
                cam.start()
                time.sleep(0.5)  # Allow sensor to settle

                # Wrap in an adapter so callers use the same .read() / .release() API
                class _Picamera2Adapter:
                    def __init__(self, picam):
                        self._cam = picam
                        self.opened = True

                    def isOpened(self):
                        return self.opened

                    def read(self):
                        try:
                            import numpy as np
                            frame = self._cam.capture_array()
                            # picamera2 RGB888 → cv2 expects BGR
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            return True, frame
                        except Exception:
                            return False, None

                    def release(self):
                        try:
                            self._cam.stop()
                            self._cam.close()
                        except Exception:
                            pass
                        self.opened = False

                return _Picamera2Adapter(cam)
            except Exception as e:
                self.log("CAM_ERR", f"picamera2 failed to open: {e}. Falling back to VideoCapture.")

        # Fallback: USB webcam
        cap = cv2.VideoCapture(0)
        return cap

    def verify_bottle(self) -> tuple[bool, str, str, float]:
        """
        Uses the camera and YOLOv11 model to verify and classify the inserted bottle.
        Returns a 4-tuple: (is_valid, brand_name, size_category, confidence_score)
        confidence_score is 0.0 when is_valid=False.
        """
        if not self.cv_available or self.model is None:
            self.log("CV", "CV engine or YOLO model weights missing. Failing verification.")
            return False, "None", "None", 0.0

        self.log("CAM", "Starting camera module...")
        cap = self._open_camera()
        if not cap.isOpened():
            self.log("CAM_ERR", "Camera not detected. Failing verification.")
            return False, "None", "None", 0.0

        self.log("CV", "Analyzing image frames with YOLOv11 to confirm bottle...")
        
        detections = []
        try:
            # Read up to 10 frames to ensure we are sure it's a bottle
            for _ in range(10):
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Camera is mounted upside down, rotate it 180 degrees
                # frame = cv2.rotate(frame, cv2.ROTATE_180)
                
                # Show camera feed for debugging only if running in CLI mode
                if SHOW_CV_WINDOW:
                    cv2.imshow("RVM Camera Feed - Verifying", frame)
                    cv2.waitKey(1)
                
                # Use a reasonable confidence threshold
                results = self.model.predict(frame, conf=0.55, verbose=False)
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = self.model.names[cls_id]
                        detections.append((class_name, conf))
                        break # Only take the first confident box per frame
                
                # Break early if we have 3 consistent detections
                if len(detections) >= 3:
                    class_counts = {}
                    for cls_name, _ in detections:
                        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                    if max(class_counts.values()) >= 3:
                        break
                        
                time.sleep(0.05) # Small delay between frames
        except Exception as e:
            self.log("CV_ERR", f"Prediction execution failed: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()

        # Check if we have enough consistent detections (at least 3 frames)
        if len(detections) >= 3:
            class_counts = {}
            for cls_name, conf in detections:
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                
            best_class = max(class_counts, key=class_counts.get)
            best_conf = max([conf for name, conf in detections if name == best_class])
            
            self.log("CV", f"Confirmed match: '{best_class}' (seen {class_counts[best_class]} times, max conf {best_conf:.2f})")
            
            # Parse brand and size from name (e.g. 'Le Minerale 600ml')
            parts = best_class.split()
            if len(parts) >= 2:
                size = parts[-1]
                brand = " ".join(parts[:-1])
            else:
                brand = best_class
                size = "Medium"
                
            return True, brand, size, best_conf

        self.log("CV", "No valid beverage bottles consistently recognized in the chute.")
        return False, "None", "None", 0.0


# --- HEARTBEAT ---
def _heartbeat_worker(hw, backend_url, machine_id, api_key, interval=30):
    """Runs in daemon thread. POSTs heartbeat every `interval` seconds. Never raises."""
    while True:
        try:
            payload = {
                "machineUuid": machine_id,
                "isCapacityFull": hw.is_bin_full(),
            }
            resp = requests.post(
                f"{backend_url}/api/rpi/machine/heartbeat",
                headers={"X-API-Key": api_key},
                json=payload,
                timeout=10,
            )
            if resp.status_code not in (200, 201):
                logging.warning(
                    "[HEARTBEAT] Server returned %s", resp.status_code
                )
        except Exception as exc:
            logging.warning("[HEARTBEAT] POST failed: %s", exc)
        time.sleep(interval)


def start_heartbeat_thread(hw):
    """Creates and starts a daemon heartbeat thread. Returns the thread."""
    t = threading.Thread(
        target=_heartbeat_worker,
        args=(hw, BACKEND_URL, MACHINE_ID, API_KEY),
        daemon=True,
    )
    t.start()
    return t


# --- SESSION HELPERS ---

def wait_for_action(ui_bridge, accepted_actions, timeout_seconds=300.0):
    """
    Polls ui_bridge for a message matching one of the accepted_actions.

    Returns the action string on match, or None on timeout / UI disconnect.
    Timeout is enforced with a monotonic clock; each poll sub-interval is 0.5 s.
    (Req 4.1, 4.5)
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not ui_bridge.clients:
            return None
        msg = ui_bridge.get_message(timeout=0.5)
        if msg is not None:
            action = msg.get("action")
            if action in accepted_actions:
                return action
    return None


# --- MAIN FIRMWARE PROCESS ---
def run_ecopoints_firmware(hw: "HardwareInterface"):
    global physical_bottle_inserted
    
    hw.boot_sequence()
    start_heartbeat_thread(hw)

    # --- IDENTIFY: obtain org_id for points config fetch ---
    org_id = None
    try:
        identify_resp = requests.post(
            f"{BACKEND_URL}/api/rpi/machine/identify",
            headers={"X-API-Key": API_KEY},
            json={"machineUuid": MACHINE_ID},
            timeout=10,
        )
        if identify_resp.status_code in (200, 201):
            org_id = identify_resp.json().get("machine", {}).get("organizationId")
            hw.log("NET", f"Machine identified. org_id={org_id}")
        else:
            hw.log("NET", f"Identify returned HTTP {identify_resp.status_code}. org_id unknown; using default points.")
    except Exception as _exc:
        hw.log("NET", f"Identify call failed: {_exc}. Using default points config.")

    points_config = fetch_points_config(BACKEND_URL, org_id, API_KEY, fallback=POINTS_DEFAULT)

    user_total_points = 0

    while True:
        # --- TEST ISOLATION STOP POINT ---
        # Tests set _firmware_stop_event to cleanly break the infinite loop
        # without killing the process.  In production this is never set.
        if _firmware_stop_event.is_set():
            hw.log("SYS", "Stop event received. Firmware loop exiting (test isolation).")
            return

        # --- STATE: IDLE / WELCOME ---
        # Wait for at least one Kiosk UI client to connect first
        if not ui_bridge.clients:
            hw.log("SYS", "Waiting for Kiosk UI client to connect on ws://localhost:8765 ...")
            while not ui_bridge.clients:
                if _firmware_stop_event.is_set():
                    hw.log("SYS", "Stop event received during client wait. Exiting.")
                    return
                time.sleep(1)
            hw.log("SYS", "Kiosk UI client connected! Starting session...")

        hw.log("SYS", "State: IDLE")

        # Initial check for full storage capacity (disabled to keep start button active)
        # is_full = hw.is_bin_full()
        # if is_full:
        #     hw.display_ui("Sorry, machine is currently full. Please try again later.", "SET_BIN_FULL")
        #     hw.log("SYS", "Capacity Reached. System suspended for 5s.")
        #     time.sleep(5)
        #     continue  # Restart loop to check if bin was cleared

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
                
            # If the bin becomes full while idling, suspend system (disabled to keep start button active)
            # if hw.is_bin_full():
            #     hw.display_ui("Sorry, machine is currently full. Please try again later.", "SET_BIN_FULL")
            #     hw.log("SYS", "Capacity Reached while idling. Suspending...")
            #     time.sleep(5)
            #     bin_became_full = True
            #     break
                
            msg = ui_bridge.get_message(timeout=0.5)
            if msg and msg.get("action") == "WAKE":
                break
                
        # if bin_became_full:
        #     continue

        ui_bridge.broadcast("WAKE")

        def wake_server():
            try:
                requests.get(f"{BACKEND_URL}/", timeout=5)
            except Exception:
                pass
        threading.Thread(target=wake_server, daemon=True).start()
        hw.log("NET", "Ping sent to wake backend server...")

        # --- STATE: QR SCANNING ---
        if hw.gpio_available:
            GPIO.output(PIN_IN_PROGRESS, GPIO.LOW) # Turn ON indicator (active-LOW)
            
        hw.set_scanner_power(True)
        time.sleep(1.5)  # Give USB scanner time to boot
        
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
                # 1. Authenticate QR Code
                auth_resp = requests.post(f"{BACKEND_URL}/api/rpi/authenticate", headers={"X-API-Key": API_KEY}, json={
                    "qrPayload": scanned_qr_data,
                    "machineUuid": MACHINE_ID
                })
                
                if auth_resp.status_code in [200, 201]:
                    auth_data = auth_resp.json()
                    wallet_id = auth_data.get("walletId")
                    user_data = auth_data.get("user", {})
                    account_name = user_data.get("name", "Unknown")
                    role = user_data.get("role", "user")

                    if role in ["technician", "superadmin", "head_admin"]:
                        hw.log("API", f"Admin {account_name} authenticated.")
                        ui_bridge.broadcast("ADMIN_LOGIN", {"userName": account_name})
                        
                        hw.log("SYS", "Waiting for admin actions to complete...")
                        while True:
                            if not ui_bridge.clients:
                                break
                            msg = ui_bridge.get_message(timeout=0.5)
                            if msg:
                                action = msg.get("action")
                                if action in ["SYSTEM_CLEAR", "CANCEL"]:
                                    break
                                elif action == "SUBMIT_LOG":
                                    payload = msg.get("payload", {})
                                    log_payload = {
                                        "machineUuid": MACHINE_ID,
                                        "actionType": payload.get("actionType"),
                                        "status": payload.get("status"),
                                        "notes": payload.get("notes"),
                                        "performedById": user_data.get("id")
                                    }
                                    hw.log("API", f"Submitting machine log: {log_payload}")
                                    try:
                                        log_resp = requests.post(f"{BACKEND_URL}/api/rpi/logs/machines", headers={"X-API-Key": API_KEY}, json=log_payload)
                                        if log_resp.status_code in [200, 201]:
                                            hw.log("API", "Machine log successfully submitted.")
                                        else:
                                            hw.log("API_ERR", f"Failed to submit machine log: Server returned {log_resp.status_code}")
                                    except Exception as e:
                                        hw.log("API_ERR", f"Could not sync machine log to backend: {e}")

                        qr_flow_complete = "TIMEOUT"
                        break
                    
                    # 2. Start Session
                    session_resp = requests.post(f"{BACKEND_URL}/api/rpi/session/start", headers={"X-API-Key": API_KEY}, json={
                        "walletId": wallet_id,
                        "machineUuid": MACHINE_ID
                    })
                    
                    if session_resp.status_code in [200, 201]:
                        session_data = session_resp.json()
                        session_id = session_data.get("session", {}).get("id")
                        hw.log("API", f"User {account_name} authenticated. Session {session_id} started.")
                        ui_bridge.broadcast("LOGIN_SUCCESS", {"userName": account_name})
                        qr_flow_complete = True
                    else:
                        hw.display_ui("Session start error.")
                        hw.log("WARN", f"Failed to start session. Status code: {session_resp.status_code}")
                        ui_bridge.broadcast("LOGIN_DENIED")
                        qr_flow_complete = "TIMEOUT"
                        break
                else:
                    hw.display_ui("QR not recognized. Please try again.")
                    hw.log("WARN", f"Backend rejected token. Status code: {auth_resp.status_code}")
                    ui_bridge.broadcast("LOGIN_DENIED")
                    qr_flow_complete = "TIMEOUT"
                    break
            except requests.exceptions.RequestException as e:
                hw.log("API_ERR", f"Could not connect to backend: {e}")
                hw.display_ui("Network error. Please try again later.")
                ui_bridge.broadcast("LOGIN_DENIED")
                qr_flow_complete = "TIMEOUT"
                break
        hw.set_scanner_power(False)

        if qr_flow_complete == "TIMEOUT":
            if hw.gpio_available:
                GPIO.output(PIN_IN_PROGRESS, GPIO.HIGH) # Turn OFF indicator
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

            hw.log("SYS", "Waiting for bottle insertion (Camera Auto-Detection, Hardware Sensor, or UI Simulator)...")
            user_inserted = False
            
            # Start camera for auto-detection
            cap = None
            consecutive_detections = 0
            if hw.cv_available and hw.model:
                hw.log("CAM", "Starting camera module for auto-detection...")
                cap = hw._open_camera()
            
            while True:
                if not ui_bridge.clients:
                    hw.log("SYS", "UI client disconnected during transaction.")
                    user_inserted = False
                    break
                
                # Check for live door openings via Homing Sensor (Dispenser Door)
                # HIGH = off home position = door open
                if hw.gpio_available and GPIO.input(PIN_MOTOR_HOME) == GPIO.HIGH:
                    hw.display_ui("Door Open. Please insert bottle.", "SET_DOOR_OPEN")
                    hw.log("MECH", "Dispenser door opened by user!")
                    
                    while GPIO.input(PIN_MOTOR_HOME) == GPIO.HIGH:
                        time.sleep(0.1)
                        
                    hw.display_ui("Door Closed. Processing...", "DOOR_CLOSED")
                    hw.log("SYS", "Dispenser door closed. Proceeding to verification.")
                    user_inserted = True
                    break
                
                # Check for physical hardware sensor interrupt
                if physical_bottle_inserted:
                    hw.log("GPIO", "Bottle insertion detected via hardware pulse.")
                    physical_bottle_inserted = False  # Consume trigger
                    user_inserted = True
                    break
                
                # Check Camera feed for bottle detection
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        # Camera is mounted upside down, rotate it 180 degrees
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                        
                        if SHOW_CV_WINDOW:
                            cv2.imshow("RVM Camera Feed - Waiting for Bottle", frame)
                            cv2.waitKey(1)
                        
                        detected_in_frame = False
                        results = hw.model.predict(frame, conf=0.6, verbose=False)
                        for result in results:
                            if len(result.boxes) > 0:
                                detected_in_frame = True
                                break
                                
                        if detected_in_frame:
                            consecutive_detections += 1
                            if consecutive_detections >= 4:
                                cls_id = int(results[0].boxes[0].cls[0])
                                class_name = hw.model.names[cls_id]
                                hw.log("CV", f"Auto-detected {class_name} consistently! Triggering insertion.")
                                user_inserted = True
                                break
                        else:
                            consecutive_detections = 0
                
                if user_inserted:
                    break
                
                # Very short timeout so the camera read isn't blocked
                msg = ui_bridge.get_message(timeout=0.01)
                if msg:
                    if msg.get("action") == "CANCEL":
                        user_inserted = False
                        break
                    elif msg.get("action") == "BOTTLE_INSERTED":
                        hw.log("SYS", "Bottle insertion triggered via UI simulation button.")
                        user_inserted = True
                        break
            
            # Release camera so verify_bottle can safely reopen it
            if cap:
                cap.release()
                cv2.destroyAllWindows()
                time.sleep(0.5)  # Give OS time to free the camera resource
            
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
            hw.spin_motor()  # default steps=200
            
            # Execute CV classification
            if hw.gpio_available:
                GPIO.output(PIN_STROBE, GPIO.LOW) # Turn ON
            is_valid, brand_name, size_category, confidence = hw.verify_bottle()
            if hw.gpio_available:
                GPIO.output(PIN_STROBE, GPIO.HIGH) # Turn OFF
            
            if not is_valid:
                hw.log("ERR", "Object Classification: INVALID/FOREIGN OBJECT")
                hw.display_ui("Transaction Denied: Invalid Item Detected", "VERIFY_FAIL", {
                    "reason": "Non-recyclable material or unrecognized bottle brand."
                })
                hw.log("MECH", "Unlocking door for removal...")
                
                # Wait for user to decide to try again or finish (Req 4.1, 4.2, 4.3, 4.6)
                hw.log("SYS", "Waiting for user action on rejection screen...")
                action = wait_for_action(ui_bridge, ["REPEAT_READY", "FINISH", "CANCEL"])
                if action is None:
                    # Timeout path (Req 4.2, 4.3, 4.6)
                    hw.log("SYS", "Session timed out on rejection screen.")
                    try:
                        requests.post(
                            f"{BACKEND_URL}/api/rpi/session/{session_id}/end",
                            json={"status": "timed_out", "machineUuid": MACHINE_ID},
                            headers={"X-API-Key": API_KEY},
                            timeout=10,
                        )
                    except Exception as e:
                        hw.log("NET_ERR", f"Session end (timed_out) failed: {e}")
                    ui_bridge.broadcast("ADVANCE_THANK_YOU")
                    transacting = False
                    break

                if action == "REPEAT_READY":
                    continue
                else:
                    transacting = False
                    break
            else:
                hw.log("INFO", f"Verified successfully: {brand_name} ({size_category})")
                
                # Map size token to points via fetched config (falls back to POINTS_DEFAULT)
                best_class = f"{brand_name} {size_category}"
                size_token = best_class.split()[-1].lower() if best_class else ""
                points = points_config.get(size_token, POINTS_DEFAULT.get(size_token, 5))

                user_total_points += points
                
                hw.log("DB", f"Sending deposit log: {brand_name} (+{points} pts)")
                try:
                    response = requests.post(f"{BACKEND_URL}/api/rpi/session/{session_id}/deposit", headers={"X-API-Key": API_KEY}, json={
                        "machineUuid": MACHINE_ID,
                        "detectedClass": brand_name,
                        "confidenceScore": round(confidence, 4),
                        "pointsAwarded": points,
                        "status": "Accepted"
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
                
                # Wait for user choice (another bottle or finish) (Req 4.1, 4.2, 4.3, 4.6)
                hw.log("SYS", "Waiting for user action (Repeat/Finish)...")
                action = wait_for_action(ui_bridge, ["REPEAT_READY", "FINISH"])
                if action is None:
                    # Timeout path (Req 4.2, 4.3, 4.6)
                    hw.log("SYS", "Session timed out on acceptance screen.")
                    try:
                        requests.post(
                            f"{BACKEND_URL}/api/rpi/session/{session_id}/end",
                            json={"status": "timed_out", "machineUuid": MACHINE_ID},
                            headers={"X-API-Key": API_KEY},
                            timeout=10,
                        )
                    except Exception as e:
                        hw.log("NET_ERR", f"Session end (timed_out) failed: {e}")
                    ui_bridge.broadcast("ADVANCE_THANK_YOU")
                    transacting = False
                    break

                if action == "REPEAT_READY":
                    hw.log("SYS", "User selected transact again. Looping...")
                    continue
                else:
                    transacting = False

        # --- STATE: END OF SESSION ---
        hw.display_ui(f"Your Total Points : {user_total_points} pts")
        hw.log("DB", "Committing session to database...")
        if session_id:
            try:
                end_resp = requests.post(f"{BACKEND_URL}/api/rpi/session/{session_id}/end", headers={"X-API-Key": API_KEY}, json={
                    "status": "completed",
                    "machineUuid": MACHINE_ID
                })
                if end_resp.status_code in [200, 201]:
                    hw.log("DB", "Session successfully committed.")
                else:
                    hw.log("DB", f"Failed to commit session: Server returned {end_resp.status_code}")
            except Exception as e:
                hw.log("API_ERR", f"Failed to finalize session: {e}")
                
        hw.log("SYS", "Session Finalized.")
        if hw.gpio_available:
            GPIO.output(PIN_IN_PROGRESS, GPIO.HIGH) # Turn OFF indicator
        hw.display_ui("Thank you for using EcoPoints.", "ADVANCE_THANK_YOU")

        # Reset session point trackers
        user_total_points = 0
        time.sleep(8)


if __name__ == "__main__":
    _hw = None
    try:
        _hw = HardwareInterface()
        run_ecopoints_firmware(_hw)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown initiated by user.")
    finally:
        if _hw is not None:
            # shutdown_gpio() drives LED pins HIGH (OFF) BEFORE releasing them
            # to INPUT/floating mode, preventing active-LOW LEDs from staying lit.
            _hw.shutdown_gpio()
            print("[GPIO] Pins returned to safe state.")
        elif GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception as e:
                print(f"[GPIO_ERR] Cleanup failed: {e}")