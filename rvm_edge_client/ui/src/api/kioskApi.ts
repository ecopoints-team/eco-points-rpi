// Mock API — all functions return fake data with simulated delays.
// Swap these out for real HTTP/WebSocket calls once the backend is ready.

const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

// ── Toggle these flags to simulate different outcomes ──
const MOCK_LOGIN_SUCCESS = true;
const MOCK_VERIFY_SUCCESS = true;

export async function loginWithQR(
  _token: string
): Promise<{ success: boolean; userName: string; role?: string }> {
  await delay(1200);
  if (MOCK_LOGIN_SUCCESS) {
    const isTech = _token.toLowerCase().includes('admin') || _token.toLowerCase().includes('tech');
    return { success: true, userName: isTech ? 'Admin' : 'Jay Dizon', role: isTech ? 'technician' : 'user' };
  }
  return { success: false, userName: '' };
}

export async function getVerificationResult(): Promise<{
  accepted: boolean;
  points: number;
  bottleCount: number;
  reason?: string;
}> {
  await delay(2500);
  if (MOCK_VERIFY_SUCCESS) {
    return { accepted: true, points: 15, bottleCount: 3 };
  }
  return {
    accepted: false,
    points: 0,
    bottleCount: 0,
    reason: 'Non-recyclable material detected.',
  };
}

export async function getSystemStatus(): Promise<{
  binFull: boolean;
  doorOpen: boolean;
}> {
  await delay(200);
  return { binFull: false, doorOpen: false };
}
