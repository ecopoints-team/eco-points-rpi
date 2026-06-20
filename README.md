# EcoPoints Raspberry Pi & Local Development System

Complete setup guide for installing, configuring, and running the EcoPoints Reverse Vending Machine (RVM) firmware and Kiosk UI on both **Windows (Development/Simulation)** and a **Raspberry Pi 5 (Production)**.

---

## 🏗️ System Architecture

The EcoPoints RVM system is designed with a unified, production-ready architecture:

1. **Edge Client Firmware (`rvm_edge_client/`)**: The core Python controller daemon. It directly interfaces with physical Raspberry Pi 5 GPIO pins (handling bottle insertion, door sensors, and storage level), processes real camera input using OpenCV, classifies beverage bottles via a trained YOLOv11 model (`best.pt`), handles backend API synchronization, and coordinates UI transitions.
2. **Kiosk UI (`rvm_edge_client/ui/`)**: A React Native (Expo) web application that serves as the touch-screen interface for users to scan QR codes, view deposit statistics, and complete transactions.

```
       ┌────────────────────────┐
       │   EcoPoints Backend    │
       │    (Flask / Cloud)     │
       └───────────▲────────────┘
                   │ HTTP API
       ┌───────────▼────────────┐
       │  Edge Client Firmware  │
       │  (main.py + GPIO + CV) │
       └───────────▲────────────┘
                   │ WebSockets (Port 8765)
┌──────────────────▼──────────────────┐
│              Kiosk UI               │
│        (React Native / Expo)        │
└─────────────────────────────────────┘
```

---

## 🔌 Hardware Wiring Guide (Raspberry Pi 5)

Connect your sensors to the Raspberry Pi 5 GPIO pins using the **BCM numbering schema**:

| Sensor | GPIO Pin | Physical Pin | Default State | Description / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Bottle Inserted** | `GPIO 17` | Pin 11 | `LOW` | Sends a short `HIGH` pulse when a bottle passes through the chute. |
| **Bin Full** | `GPIO 27` | Pin 13 | `LOW` | Reads `HIGH` when the storage limit sensor is blocked. |
| **Door Open** | `GPIO 22` | Pin 15 | `LOW` | Reads `HIGH` when the magnetic safety door is opened. |
| **Ground** | `GND` | Pin 9, 14, 20... | — | Common ground reference for all hardware components. |

> [!IMPORTANT]
> All GPIO pins are configured with internal **pull-down resistors** (`PUD_DOWN`) in the code, ensuring they default to `LOW` when not triggered.

---

## 🛠️ Step-by-Step Installation (Windows CMD)

Follow these steps using the **Windows Command Prompt (`cmd.exe`)** to set up your local development and simulation environment.

### Prerequisites
Make sure you have the following installed on your Windows machine:
- **Python 3.10+** (Ensure you check "Add Python to PATH" during installation)
- **Node.js (v18+)** and npm
- **Git**

---

### Step 1: Set Up the Edge Client Firmware

1. Navigate to the `rvm_edge_client` directory:
   ```cmd
   cd rvm_edge_client
   ```
2. Create a Python virtual environment:
   ```cmd
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```cmd
   call venv\Scripts\activate
   ```
4. Install Python dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
5. Configure your environment variables:
   ```cmd
   copy .env.example .env
   ```
6. Open the newly created `.env` file in a text editor (e.g. Notepad, VS Code) and update the backend URL and details:
   - `BACKEND_URL`: URL of the cloud backend (e.g., `http://127.0.0.1:5000`)
   - `MACHINE_ID`: Unique machine ID (e.g., `RVM-PU-01`)
   - `LOCATION`: Location description (e.g., `Institute of Technology`)
   - `CLI_MODE`: Set to `true` to run without a UI, or `false` for normal UI-driven mode
   - `API_KEY`: The API key to authenticate requests with the Eco-Points backend
   - `QR_HMAC_SECRET`: The shared secret used to sign mock user IDs in simulation mode

---

### Step 2: Set Up the Kiosk UI

1. Navigate to the `ui` directory:
   ```cmd
   cd ui
   ```
2. Install npm modules:
   ```cmd
   npm install
   ```

---

## 🚀 Running the System (Windows CMD)

To develop and test on your computer without physical sensors, run the system in **Simulation (Development) Mode**.

### 1. Run the Firmware Simulation
Open a Command Prompt, navigate to the `rvm_edge_client` directory, activate the environment, and start the controller:
```cmd
cd rvm_edge_client
call venv\Scripts\activate
python main.py
```
*Note: Because `RPi.GPIO` and cameras are typically absent on development PCs, the script automatically falls back to simulating computer vision models and uses the UI's simulation button for triggers.*

### 2. Start the Kiosk UI
Open another Command Prompt, navigate to the `ui` directory, and start the web development server:
```cmd
cd rvm_edge_client\ui
npm run web
```
This will automatically compile and serve the frontend. Open your web browser at `http://localhost:8081`. You can trigger bottle deposits using the **"Simulate: Bottle Inserted"** button at the bottom-right corner of the active session screen.

---

## ⚙️ Raspberry Pi Production Deployment

On the actual Raspberry Pi 5 with physical hardware connected, you will use the Linux Terminal/Bash.

### 1. Run Services
- **Start Firmware Daemon**:
  ```bash
  cd rvm_edge_client
  source venv/bin/activate
  python main.py
  ```
- **Start Kiosk UI**:
  ```bash
  cd rvm_edge_client/ui
  npm run web
  ```

### 2. Auto-Start on Boot (systemd)

#### Firmware Daemon Service
Create `/etc/systemd/system/ecopoints-firmware.service`:
```ini
[Unit]
Description=EcoPoints Edge Client Firmware Daemon
After=network.target

[Service]
ExecStart=/home/pi/eco-points-rpi/rvm_edge_client/venv/bin/python /home/pi/eco-points-rpi/rvm_edge_client/main.py
WorkingDirectory=/home/pi/eco-points-rpi/rvm_edge_client
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ecopoints-firmware.service
sudo systemctl start ecopoints-firmware.service
```

#### Auto-Start Chromium Browser in Kiosk Mode
1. Create autostart directory:
   ```bash
   mkdir -p ~/.config/autostart
   ```
2. Create `~/.config/autostart/kiosk.desktop`:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=EcoPoints Kiosk
   Exec=chromium --kiosk --noerrdialogs --disable-infobars --app=http://localhost:8081
   ```

---

## 🔍 Troubleshooting

- **Address in Use Error (`OSError: [Errno 98]` or `OSError: [WinError 10048]`)**:
  Ensure no other services are running on port `8765` which is required for the WebSocket Kiosk UI Bridge.
- **Python Commands Not Recognized**:
  If the `python` command fails, try using `py` or `python3` instead, and verify that Python is added to your Windows Environment Variables Path.
