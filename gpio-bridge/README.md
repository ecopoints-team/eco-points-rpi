# EcoPoints GPIO Bridge

Python WebSocket server that reads Raspberry Pi 5 GPIO pins and broadcasts hardware events to the kiosk UI.

## Wiring (BCM numbering)

| Sensor | GPIO Pin | Signal |
|---|---|---|
| Bottle inserted | GPIO 17 | HIGH pulse on detection |
| Bin full | GPIO 27 | HIGH while sensor triggered |
| Door open | GPIO 22 | HIGH while door is open |
| Ground | Any GND | Common ground for all sensors |

> All pins use internal pull-down resistors (`PUD_DOWN`), so they read LOW by default.

## Setup (on Raspberry Pi 5)

```bash
cd gpio-bridge
pip3 install -r requirements.txt
python3 ws_server.py
```

## Auto-start on Boot (systemd)

Create `/etc/systemd/system/ecopoints-gpio.service`:

```ini
[Unit]
Description=EcoPoints GPIO Bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/eco-points-machine/gpio-bridge/ws_server.py
WorkingDirectory=/home/pi/eco-points-machine/gpio-bridge
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then enable it:
```bash
sudo systemctl enable ecopoints-gpio
sudo systemctl start ecopoints-gpio
```

## Launch Kiosk UI

```bash
cd kiosk
npm run web &
sleep 5
chromium-browser --kiosk --app=http://localhost:8081
```
or 
cd kiosk
npm install 
npm start


## Simulation Mode

When `RPi.GPIO` is not available (e.g., on a dev machine), the bridge runs in simulation mode — all sensors read LOW and no GPIO setup is performed. You can still run `ws_server.py` and connect to it.

## WebSocket Message Format

All messages are JSON objects sent to `ws://localhost:8765`:

| Event | Trigger |
|---|---|
| `{ "event": "BOTTLE_INSERTED" }` | Rising edge on GPIO 17 |
| `{ "event": "BIN_FULL" }` | GPIO 27 goes HIGH |
| `{ "event": "SYSTEM_CLEAR", "sensor": "bin" }` | GPIO 27 goes LOW |
| `{ "event": "DOOR_OPEN" }` | GPIO 22 goes HIGH |
| `{ "event": "SYSTEM_CLEAR", "sensor": "door" }` | GPIO 22 goes LOW |
