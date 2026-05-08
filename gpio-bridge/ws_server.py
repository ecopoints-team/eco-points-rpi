"""
ws_server.py — EcoPoints Kiosk GPIO WebSocket Bridge
Runs on Raspberry Pi 5. Reads GPIO pins and broadcasts events
to all connected WebSocket clients (the React Native kiosk UI).

Usage:
    python3 ws_server.py

The kiosk app connects to ws://localhost:8765 and receives JSON messages:
    { "event": "BOTTLE_INSERTED" }
    { "event": "BIN_FULL" }
    { "event": "DOOR_OPEN" }
    { "event": "SYSTEM_CLEAR", "sensor": "bin" | "door" }
"""

import asyncio
import json
import logging
import websockets
from gpio_listener import GPIOListener
from config import WS_HOST, WS_PORT

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)

CLIENTS: set = set()


async def broadcast(message: dict):
    if not CLIENTS:
        return
    data = json.dumps(message)
    await asyncio.gather(*(client.send(data) for client in CLIENTS), return_exceptions=True)


async def handler(websocket):
    CLIENTS.add(websocket)
    logger.info(f"Client connected: {websocket.remote_address} | total={len(CLIENTS)}")
    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.discard(websocket)
        logger.info(f"Client disconnected | total={len(CLIENTS)}")


async def gpio_loop(listener: GPIOListener):
    """Poll GPIO state and broadcast changes."""
    prev_bin_full = False
    prev_door_open = False

    while True:
        bin_full = listener.is_bin_full()
        door_open = listener.is_door_open()

        if bin_full and not prev_bin_full:
            logger.info("EVENT: BIN_FULL")
            await broadcast({"event": "BIN_FULL"})
        elif not bin_full and prev_bin_full:
            logger.info("EVENT: SYSTEM_CLEAR (bin)")
            await broadcast({"event": "SYSTEM_CLEAR", "sensor": "bin"})

        if door_open and not prev_door_open:
            logger.info("EVENT: DOOR_OPEN")
            await broadcast({"event": "DOOR_OPEN"})
        elif not door_open and prev_door_open:
            logger.info("EVENT: SYSTEM_CLEAR (door)")
            await broadcast({"event": "SYSTEM_CLEAR", "sensor": "door"})

        prev_bin_full = bin_full
        prev_door_open = door_open

        await asyncio.sleep(listener.poll_interval)


async def main():
    listener = GPIOListener()
    listener.setup()

    # Register edge-detect callback for bottle inserted (pulse signal)
    listener.on_bottle_inserted(
        lambda: asyncio.get_event_loop().call_soon_threadsafe(
            asyncio.ensure_future, broadcast({"event": "BOTTLE_INSERTED"})
        )
    )

    logger.info(f"GPIO WebSocket server starting on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handler, WS_HOST, WS_PORT):
        await asyncio.gather(
            gpio_loop(listener),
            asyncio.Future(),  # run forever
        )


if __name__ == "__main__":
    asyncio.run(main())
