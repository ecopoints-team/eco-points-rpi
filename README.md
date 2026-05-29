# EcoPoints RPI

Raspberry Pi firmware and Kiosk UI for the EcoPoints RVM system.

## Project Structure
- `rvm_edge_client/main.py`: Core firmware logic and WebSocket bridge.
- `rvm_edge_client/ui/`: React Native (Expo) Kiosk UI.
- `gpio-bridge/`: Python GPIO listener.

## Running the System

### 1. Start the Firmware
```bash
cd rvm_edge_client
python main.py
```

### 2. Start the Kiosk UI
```bash
cd rvm_edge_client/ui
npm install
npx expo start --web
```
Overall program. Website, Admin Dashboard, Machine Program
