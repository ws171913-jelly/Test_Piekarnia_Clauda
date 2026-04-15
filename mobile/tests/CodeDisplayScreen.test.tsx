/**
 * T037 — Test ekranu CodeDisplayScreen.
 *
 * Pokrycie:
 * - renderowanie kodu 6-cyfrowego z odliczaniem TTL
 * - stan "brak salda" gdy API odrzuca z komunikatem o saldzie
 * - stan "karencja" gdy API odrzuca z komunikatem o karencji
 * - przycisk cofania
 * - ponowna próba po błędzie
 */
import React from 'react';
import {
  render,
  fireEvent,
  waitFor,
  act,
} from '@testing-library/react-native';
import CodeDisplayScreen from '../src/screens/CodeDisplayScreen';

// --- mocki ---

jest.mock('../src/services/api', () => ({
  generateCode: jest.fn(),
}));

jest.mock('../src/store/userStore', () => ({
  userStore: {
    getProfile: jest.fn(() => ({
      hrEmployeeId: 'EMP_001',
      currentBalance: 200.0,
      balanceExpiryDate: '2026-12-31',
      basket: { id: 'b1', name: 'Standard', discountPct: 20, monthlyLimitPln: null },
      locationId: 'LOC_001',
      mustChangePin: false,
      cachedAt: Date.now(),
    })),
  },
}));

import { generateCode } from '../src/services/api';

const mockGenerateCode = generateCode as jest.MockedFunction<typeof generateCode>;

// helpers
function makeExpiresAt(secondsFromNow: number): string {
  return new Date(Date.now() + secondsFromNow * 1000).toISOString();
}

// ---

describe('CodeDisplayScreen', () => {
  const onBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows loading indicator initially', () => {
    mockGenerateCode.mockReturnValue(new Promise(() => {})); // never resolves

    const { getByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(getByText('Generowanie kodu…')).toBeTruthy();
  });

  it('renders 6-digit code with space separator when active', async () => {
    mockGenerateCode.mockResolvedValueOnce({
      code: '123456',
      expires_at: makeExpiresAt(900),
    } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(await findByText('123 456')).toBeTruthy();
  });

  it('shows "KOD AKTYWNY" status when code is active', async () => {
    mockGenerateCode.mockResolvedValueOnce({
      code: '654321',
      expires_at: makeExpiresAt(900),
    } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(await findByText('KOD AKTYWNY')).toBeTruthy();
  });

  it('shows countdown timer label when active', async () => {
    mockGenerateCode.mockResolvedValueOnce({
      code: '111222',
      expires_at: makeExpiresAt(900),
    } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    // Label "Wygaśnie za MM:SS"
    const el = await findByText(/Wygaśnie za \d{2}:\d{2}/);
    expect(el).toBeTruthy();
  });

  it('shows balance and discount stats when active', async () => {
    mockGenerateCode.mockResolvedValueOnce({
      code: '999888',
      expires_at: makeExpiresAt(900),
    } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    // Saldo z profilu = 200.00 PLN
    expect(await findByText('200,00 PLN')).toBeTruthy();
    // Rabat z profilu = 20%
    expect(await findByText('20%')).toBeTruthy();
  });

  it('shows no-balance screen when API returns balance error', async () => {
    mockGenerateCode.mockRejectedValueOnce(new Error('Brak salda'));

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(await findByText('Brak salda')).toBeTruthy();
    expect(await findByText(/Twoje saldo wynosi 0,00 PLN/)).toBeTruthy();
  });

  it('shows cooldown screen when API returns karencja error', async () => {
    mockGenerateCode.mockRejectedValueOnce(
      new Error('Karencja aktywna — poczekaj jeszcze 20 minut')
    );

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(await findByText('Karencja aktywna')).toBeTruthy();
    expect(await findByText(/Karencja aktywna — poczekaj/)).toBeTruthy();
  });

  it('shows error state and retry button on generic error', async () => {
    mockGenerateCode.mockRejectedValueOnce(new Error('Błąd serwera'));

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    expect(await findByText('Błąd serwera')).toBeTruthy();
    expect(await findByText('Spróbuj ponownie')).toBeTruthy();
  });

  it('calls onBack when back button pressed', async () => {
    mockGenerateCode.mockResolvedValueOnce({
      code: '777666',
      expires_at: makeExpiresAt(900),
    } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);
    await findByText('777 666');

    fireEvent.press(await findByText('←'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('retries generateCode when "Spróbuj ponownie" is pressed', async () => {
    mockGenerateCode
      .mockRejectedValueOnce(new Error('Błąd serwera'))
      .mockResolvedValueOnce({
        code: '444555',
        expires_at: makeExpiresAt(900),
      } as any);

    const { findByText } = render(<CodeDisplayScreen onBack={onBack} />);

    const retryBtn = await findByText('Spróbuj ponownie');
    await act(async () => {
      fireEvent.press(retryBtn);
    });

    expect(await findByText('444 555')).toBeTruthy();
    expect(mockGenerateCode).toHaveBeenCalledTimes(2);
  });
});
