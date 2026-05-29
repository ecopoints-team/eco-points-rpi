import React, { createContext, useContext, useReducer, ReactNode } from 'react';

export type KioskState =
  | 'START'
  | 'IDLE'
  | 'QR_SCAN'
  | 'READY'
  | 'VERIFYING'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'THANK_YOU'
  | 'DOOR_OPEN'
  | 'DENIED'
  | 'ADMIN_MENU'
  | 'ADMIN_ACTION'
  | 'ADMIN_NOTES'
  | 'BIN_FULL_DENIED';

export type Transaction = {
  points: number;
  bottleCount: number;
};

export type KioskPayload = {
  points?: number;
  bottleCount?: number;
  userName?: string;
  reason?: string;
  previousState?: KioskState;
  sessionTransactions?: Transaction[];
  totalPoints?: number;
  totalBottles?: number;
  isBinFull?: boolean;
  adminCategory?: 'maintenance' | 'diagnostics' | 'clearing';
  adminAction?: string;
};

export type KioskAction =
  | { type: 'GO_IDLE' }
  | { type: 'WAKE' }
  | { type: 'LOGIN_SUCCESS'; payload: { userName: string } }
  | { type: 'LOGIN_DENIED' }
  | { type: 'BOTTLE_INSERTED' }
  | { type: 'VERIFY_SUCCESS'; payload: { points: number; bottleCount: number } }
  | { type: 'VERIFY_FAIL'; payload: { reason: string } }
  | { type: 'ADVANCE_THANK_YOU' }
  | { type: 'REPEAT_READY' }
  | { type: 'CLOSE_DOOR' }
  | { type: 'DOOR_CLOSED' }
  | { type: 'SET_BIN_FULL' }
  | { type: 'CLEAR_BIN_FULL' }
  | { type: 'SET_DOOR_OPEN' }
  | { type: 'SYSTEM_CLEAR' }
  | { type: 'ADMIN_LOGIN'; payload: { userName: string } }
  | { type: 'ADMIN_SELECT_CATEGORY'; payload: { category: 'maintenance' | 'diagnostics' | 'clearing' } }
  | { type: 'ADMIN_SELECT_ACTION'; payload: { action: string } }
  | { type: 'ADMIN_BACK' }
  | { type: 'ADMIN_COMPLETE' }
  | { type: 'BIN_FULL_USER_DENIED' };

type KioskStateShape = {
  screen: KioskState;
  payload: KioskPayload;
};

const initialState: KioskStateShape = {
  screen: 'START',
  payload: {},
};

const SYSTEM_SCREENS: KioskState[] = ['DOOR_OPEN'];

function reducer(state: KioskStateShape, action: KioskAction): KioskStateShape {
  switch (action.type) {
    case 'GO_IDLE':
      if (SYSTEM_SCREENS.includes(state.screen)) return state;
      return { screen: 'IDLE', payload: { isBinFull: state.payload.isBinFull, sessionTransactions: undefined, totalPoints: undefined, totalBottles: undefined } };

    case 'WAKE':
      return { screen: 'QR_SCAN', payload: { isBinFull: state.payload.isBinFull } };

    case 'LOGIN_SUCCESS':
      return { screen: 'READY', payload: { ...state.payload, userName: action.payload.userName } };

    case 'LOGIN_DENIED':
      return { screen: 'DENIED', payload: { isBinFull: state.payload.isBinFull } };

    case 'BOTTLE_INSERTED':
      return { screen: 'VERIFYING', payload: state.payload };

    case 'VERIFY_SUCCESS': {
      const newTransaction: Transaction = {
        points: action.payload.points,
        bottleCount: action.payload.bottleCount,
      };
      const updatedTransactions = [...(state.payload.sessionTransactions || []), newTransaction];
      const accumulatedPoints = state.payload.totalPoints ? state.payload.totalPoints + action.payload.points : action.payload.points;
      const accumulatedBottles = state.payload.totalBottles ? state.payload.totalBottles + action.payload.bottleCount : action.payload.bottleCount;

      return {
        screen: 'ACCEPTED',
        payload: {
          ...state.payload,
          points: action.payload.points,
          bottleCount: action.payload.bottleCount,
          sessionTransactions: updatedTransactions,
          totalPoints: accumulatedPoints,
          totalBottles: accumulatedBottles,
        },
      };
    }

    case 'VERIFY_FAIL':
      return {
        screen: 'REJECTED',
        payload: { ...state.payload, reason: action.payload.reason },
      };

    case 'ADVANCE_THANK_YOU':
      return {
        screen: 'THANK_YOU',
        payload: {
          ...state.payload,
          sessionTransactions: state.payload.sessionTransactions,
          totalPoints: state.payload.totalPoints,
          totalBottles: state.payload.totalBottles,
        },
      };

    case 'REPEAT_READY':
      return { screen: 'READY', payload: state.payload };

    case 'CLOSE_DOOR':
      return { screen: state.payload.previousState ?? 'START', payload: { ...state.payload, previousState: undefined } };

    case 'DOOR_CLOSED':
      if (state.screen === 'DOOR_OPEN') {
        return { screen: state.payload.previousState ?? 'READY', payload: { ...state.payload, previousState: undefined } };
      }
      return state;

    case 'SET_BIN_FULL':
      return {
        screen: state.screen,
        payload: { ...state.payload, isBinFull: true },
      };

    case 'CLEAR_BIN_FULL':
      return {
        screen: state.screen,
        payload: { ...state.payload, isBinFull: false },
      };

    case 'SET_DOOR_OPEN':
      return {
        screen: 'DOOR_OPEN',
        payload: { ...state.payload, previousState: state.screen },
      };

    case 'SYSTEM_CLEAR':
      return { screen: 'START', payload: { isBinFull: state.payload.isBinFull } };

    // --- Admin Flow ---
    case 'ADMIN_LOGIN':
      return { screen: 'ADMIN_MENU', payload: { userName: action.payload.userName, isBinFull: state.payload.isBinFull } };

    case 'ADMIN_SELECT_CATEGORY':
      return { screen: 'ADMIN_ACTION', payload: { ...state.payload, adminCategory: action.payload.category } };

    case 'ADMIN_SELECT_ACTION':
      return { screen: 'ADMIN_NOTES', payload: { ...state.payload, adminAction: action.payload.action } };

    case 'ADMIN_BACK':
      if (state.screen === 'ADMIN_NOTES') {
        return { screen: 'ADMIN_ACTION', payload: { ...state.payload, adminAction: undefined } };
      }
      if (state.screen === 'ADMIN_ACTION') {
        return { screen: 'ADMIN_MENU', payload: { ...state.payload, adminCategory: undefined } };
      }
      return state;

    case 'ADMIN_COMPLETE':
      return { screen: 'START', payload: { isBinFull: false } };

    case 'BIN_FULL_USER_DENIED':
      return { screen: 'BIN_FULL_DENIED', payload: { isBinFull: true } };

    default:
      return state;
  }
}

type KioskContextType = {
  screen: KioskState;
  payload: KioskPayload;
  dispatch: React.Dispatch<KioskAction>;
};

const KioskContext = createContext<KioskContextType | null>(null);

export function KioskProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <KioskContext.Provider value={{ screen: state.screen, payload: state.payload, dispatch }}>
      {children}
    </KioskContext.Provider>
  );
}

export function useKiosk() {
  const ctx = useContext(KioskContext);
  if (!ctx) throw new Error('useKiosk must be used inside KioskProvider');
  return ctx;
}
