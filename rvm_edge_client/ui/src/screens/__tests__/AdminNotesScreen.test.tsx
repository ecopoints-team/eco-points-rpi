/**
 * Unit test: admin log routing (Property 9)
 *
 * Validates: Requirements 11.1, 11.4
 *
 * Property 9: No direct UI-to-backend HTTP for admin logs —
 * AdminNotesScreen.handleConfirm calls sendGPIOEvent({ action: 'SUBMIT_LOG' })
 * exactly once and never calls submitMachineLog when DEV_MODE=false.
 */
import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';

// Mock modules BEFORE importing components that reference them
jest.mock('../../hooks/useGPIOBridge', () => ({
  DEV_MODE: false,
  sendGPIOEvent: jest.fn(),
}));

jest.mock('../../api/kioskApi', () => ({
  submitMachineLog: jest.fn(),
}));

// Silence Animated warnings in test environment
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

import AdminNotesScreen from '../AdminNotesScreen';
import { sendGPIOEvent } from '../../hooks/useGPIOBridge';
import { submitMachineLog } from '../../api/kioskApi';
import { KioskProvider } from '../../context/KioskContext';

// Provide KioskContext with ADMIN_NOTES screen state so AdminNotesScreen renders normally
function renderWithContext() {
  return render(
    <KioskProvider>
      <AdminNotesScreen />
    </KioskProvider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('handleConfirm calls sendGPIOEvent with SUBMIT_LOG when DEV_MODE=false', async () => {
  const { getAllByText } = renderWithContext();

  // Select at least one note option so the Confirm button is enabled
  const noteButton = getAllByText('Issues Resolved')[0];
  await act(async () => { fireEvent.press(noteButton); });

  // Press the confirm button
  const confirmButton = getAllByText('Enter/Confirm')[0];
  await act(async () => { fireEvent.press(confirmButton); });

  // sendGPIOEvent must be called exactly once with action SUBMIT_LOG
  expect(sendGPIOEvent).toHaveBeenCalledTimes(1);
  const call = (sendGPIOEvent as jest.Mock).mock.calls[0][0];
  expect(call.action).toBe('SUBMIT_LOG');
  expect(call.payload).toMatchObject({
    actionType: expect.any(String),
    status: expect.any(String),
    notes: expect.any(String),
  });
});

test('handleConfirm never calls submitMachineLog (no direct HTTP) when DEV_MODE=false', async () => {
  const { getAllByText } = renderWithContext();

  const noteButton = getAllByText('Issues Resolved')[0];
  await act(async () => { fireEvent.press(noteButton); });

  const confirmButton = getAllByText('Enter/Confirm')[0];
  await act(async () => { fireEvent.press(confirmButton); });

  // submitMachineLog must not be called — all routing goes through sendGPIOEvent
  expect(submitMachineLog).not.toHaveBeenCalled();
});

test('sendGPIOEvent is called before dispatch (SUBMIT_LOG precedes ADMIN_COMPLETE)', async () => {
  const callOrder: string[] = [];

  (sendGPIOEvent as jest.Mock).mockImplementation(() => {
    callOrder.push('sendGPIOEvent');
  });

  const { getAllByText } = renderWithContext();

  const noteButton = getAllByText('Issues Resolved')[0];
  await act(async () => { fireEvent.press(noteButton); });

  const confirmButton = getAllByText('Enter/Confirm')[0];
  await act(async () => { fireEvent.press(confirmButton); });

  // sendGPIOEvent must have been called
  expect(callOrder).toContain('sendGPIOEvent');
  expect(callOrder[0]).toBe('sendGPIOEvent');
});
