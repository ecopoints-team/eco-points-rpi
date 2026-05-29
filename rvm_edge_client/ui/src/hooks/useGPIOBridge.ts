import { useEffect, useRef } from 'react';
import { KioskAction } from '../context/KioskContext';

const WS_URL = 'ws://localhost:8765';

// Set to false to enable WS connection with Python main.py
export const DEV_MODE = false;

type GPIOEventPayload = {
  event: string;
  userName?: string;
  points?: number;
  bottleCount?: number;
  reason?: string;
};

let wsInstance: WebSocket | null = null;

export function sendGPIOEvent(data: any) {
  if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
    wsInstance.send(JSON.stringify(data));
  }
}

export function useGPIOBridge(dispatch: React.Dispatch<KioskAction>) {
  useEffect(() => {
    if (DEV_MODE) return; // skip on dev machine

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsInstance = ws;

      ws.onopen = () => console.log('[GPIO Bridge] Connected');

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as GPIOEventPayload;
          const { event } = data;
          console.log('[GPIO Bridge] Received event:', event, data);

          switch (event) {
            case 'GO_IDLE':
              dispatch({ type: 'GO_IDLE' });
              break;
            case 'WAKE':
              dispatch({ type: 'WAKE' });
              break;
            case 'LOGIN_SUCCESS':
              dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: data.userName || 'Unknown' } });
              break;
            case 'ADMIN_LOGIN':
              dispatch({ type: 'ADMIN_LOGIN', payload: { userName: data.userName || 'Admin' } });
              break;
            case 'LOGIN_DENIED':
              dispatch({ type: 'LOGIN_DENIED' });
              break;
            case 'BOTTLE_INSERTED':
              dispatch({ type: 'BOTTLE_INSERTED' });
              break;
            case 'VERIFY_SUCCESS':
              dispatch({
                type: 'VERIFY_SUCCESS',
                payload: {
                  points: data.points ?? 0,
                  bottleCount: data.bottleCount ?? 1
                }
              });
              break;
            case 'VERIFY_FAIL':
              dispatch({ type: 'VERIFY_FAIL', payload: { reason: data.reason || 'Unknown error' } });
              break;
            case 'ADVANCE_THANK_YOU':
              dispatch({ type: 'ADVANCE_THANK_YOU' });
              break;
            case 'SET_BIN_FULL':
            case 'BIN_FULL':
              dispatch({ type: 'SET_BIN_FULL' });
              break;
            case 'CLEAR_BIN_FULL':
              dispatch({ type: 'CLEAR_BIN_FULL' });
              break;
            case 'BIN_FULL_USER_DENIED':
              dispatch({ type: 'BIN_FULL_USER_DENIED' });
              break;
            case 'SET_DOOR_OPEN':
            case 'DOOR_OPEN':
              dispatch({ type: 'SET_DOOR_OPEN' });
              break;
            case 'DOOR_CLOSED':
              dispatch({ type: 'DOOR_CLOSED' });
              break;
            case 'SYSTEM_CLEAR':
              dispatch({ type: 'SYSTEM_CLEAR' });
              break;
            default:
              console.log('[GPIO Bridge] Unhandled event:', event);
          }
        } catch (err) {
          console.warn('[GPIO Bridge] Invalid message:', e.data, err);
        }
      };

      ws.onclose = () => {
        console.warn('[GPIO Bridge] Disconnected, retrying in 3s…');
        wsInstance = null;
        setTimeout(connect, 3000);
      };

      ws.onerror = (err) => console.error('[GPIO Bridge] Error', err);
    };

    connect();
    return () => {
      wsInstance?.close();
      wsInstance = null;
    };
  }, [dispatch]);
}
