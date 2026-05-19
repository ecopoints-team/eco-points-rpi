import { useEffect, useRef } from 'react';
import { KioskAction } from '../context/KioskContext';

const WS_URL = 'ws://localhost:8765';

// Set to true on dev machine (no Pi hardware) to skip WS connection
const DEV_MODE = true;

type GPIOEvent =
  | 'BOTTLE_INSERTED'
  | 'BIN_FULL'
  | 'DOOR_OPEN'
  | 'DOOR_CLOSED'
  | 'SYSTEM_CLEAR';

function eventToAction(event: GPIOEvent): KioskAction | null {
  switch (event) {
    case 'BOTTLE_INSERTED':
      return { type: 'BOTTLE_INSERTED' };
    case 'BIN_FULL':
      return { type: 'SET_BIN_FULL' };
    case 'DOOR_OPEN':
      return { type: 'SET_DOOR_OPEN' };
    case 'DOOR_CLOSED':
      return { type: 'DOOR_CLOSED' };
    case 'SYSTEM_CLEAR':
      return { type: 'SYSTEM_CLEAR' };
    default:
      return null;
  }
}

export function useGPIOBridge(dispatch: React.Dispatch<KioskAction>) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (DEV_MODE) return; // skip on dev machine

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => console.log('[GPIO Bridge] Connected');

      ws.onmessage = (e) => {
        try {
          const { event } = JSON.parse(e.data) as { event: GPIOEvent };
          const action = eventToAction(event);
          if (action) dispatch(action);
        } catch {
          console.warn('[GPIO Bridge] Invalid message:', e.data);
        }
      };

      ws.onclose = () => {
        console.warn('[GPIO Bridge] Disconnected, retrying in 3s…');
        setTimeout(connect, 3000);
      };

      ws.onerror = (err) => console.error('[GPIO Bridge] Error', err);
    };

    connect();
    return () => wsRef.current?.close();
  }, [dispatch]);
}
