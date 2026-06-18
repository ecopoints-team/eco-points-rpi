import { useEffect, useRef } from 'react';
import { KioskState, KioskAction } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from './useGPIOBridge';

const TIMERS: Partial<Record<KioskState, number>> = {
  START: 60_000,
  ACCEPTED: 8_000,
  REJECTED: 15_000,
  THANK_YOU: 5_000,
  DENIED: 15_000,
  BIN_FULL_DENIED: 15_000,
};

const ACTIONS: Partial<Record<KioskState, KioskAction>> = {
  START: { type: 'GO_IDLE' },
  ACCEPTED: { type: 'ADVANCE_THANK_YOU' },
  REJECTED: { type: 'ADVANCE_THANK_YOU' },
  THANK_YOU: { type: 'SYSTEM_CLEAR' },
  DENIED: { type: 'SYSTEM_CLEAR' },
  BIN_FULL_DENIED: { type: 'SYSTEM_CLEAR' },
};

export function useKioskTimer(
  screen: KioskState,
  dispatch: React.Dispatch<KioskAction>
) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    const duration = TIMERS[screen];
    const action = ACTIONS[screen];

    if (duration && action) {
      timerRef.current = setTimeout(() => {
        if (screen === 'ACCEPTED' || screen === 'REJECTED') {
          if (!DEV_MODE) {
            sendGPIOEvent({ action: 'FINISH' });
          }
        }
        dispatch(action);
      }, duration);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [screen, dispatch]);
}
