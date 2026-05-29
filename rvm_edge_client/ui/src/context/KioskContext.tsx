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
  | 'BIN_FULL'
  | 'DOOR_OPEN'
  | 'DENIED';

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
  | { type: 'SET_DOOR_OPEN' }
  | { type: 'SYSTEM_CLEAR' };

type KioskStateShape = {
  screen: KioskState;
  payload: KioskPayload;
};

const initialState: KioskStateShape = {
  screen: 'START',
  payload: {},
};

const SYSTEM_SCREENS: KioskState[] = ['BIN_FULL', 'DOOR_OPEN'];

function reducer(state: KioskStateShape, action: KioskAction): KioskStateShape {
  switch (action.type) {
    case 'GO_IDLE':
      if (SYSTEM_SCREENS.includes(state.screen)) return state;
      return { screen: 'IDLE', payload: { sessionTransactions: undefined, totalPoints: undefined, totalBottles: undefined } };

    case 'WAKE':
      return { screen: 'QR_SCAN', payload: {} };

    case 'LOGIN_SUCCESS':
      return { screen: 'READY', payload: { userName: action.payload.userName } };

    case 'LOGIN_DENIED':
      return { screen: 'DENIED', payload: {} };

    case 'BOTTLE_INSERTED':
      return { screen: 'VERIFYING', payload: state.payload };

    case 'VERIFY_SUCCESS':
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
      // If we're in DOOR_OPEN screen, trigger bottle verification
      if (state.screen === 'DOOR_OPEN' && state.payload.previousState === 'VERIFYING') {
        return { screen: 'VERIFYING', payload: { ...state.payload, previousState: undefined } };
      }
      return state;

    case 'SET_BIN_FULL':
      return {
        screen: 'BIN_FULL',
        payload: { previousState: state.screen },
      };

    case 'SET_DOOR_OPEN':
      return {
        screen: 'DOOR_OPEN',
        payload: { previousState: state.screen },
      };

    case 'SYSTEM_CLEAR':
      return { screen: 'START', payload: {} };

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
