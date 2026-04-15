/**
 * T017 — Test ekranu LoginScreen.
 *
 * Pokrycie:
 * - renderowanie formularza (pola, przycisk)
 * - komunikat błędu po nieudanym logowaniu
 * - stan blokady konta (banner + wyłączony przycisk)
 * - wywołanie onLoginSuccess po pomyślnym logowaniu
 */
import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import LoginScreen from '../src/screens/LoginScreen';

// --- mocki zewnętrznych zależności ---

jest.mock('../src/services/api', () => ({
  login: jest.fn(),
}));

jest.mock('../src/store/userStore', () => ({
  userStore: {
    saveSession: jest.fn(),
    getSession: jest.fn(() => null),
    getToken: jest.fn(() => null),
    clearSession: jest.fn(),
    getProfile: jest.fn(() => null),
    getTransactions: jest.fn(() => null),
  },
}));

import { login } from '../src/services/api';

const mockLogin = login as jest.MockedFunction<typeof login>;

// ------------------------------------

describe('LoginScreen', () => {
  const onLoginSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders employee ID and PIN fields', () => {
    const { getByPlaceholderText, getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    expect(getByPlaceholderText('np. 004829')).toBeTruthy();
    expect(getByPlaceholderText('••••')).toBeTruthy();
    expect(getByText('Zaloguj się')).toBeTruthy();
  });

  it('shows validation error when fields are empty', async () => {
    const { getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });
    expect(getByText('Wprowadź numer pracownika i PIN')).toBeTruthy();
    expect(onLoginSuccess).not.toHaveBeenCalled();
  });

  it('calls login() with trimmed employee ID and PIN', async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: 'tok123',
      must_change_pin: false,
    } as any);

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), '  EMP001  ');
    fireEvent.changeText(getByPlaceholderText('••••'), ' 123456 ');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    expect(mockLogin).toHaveBeenCalledWith('EMP001', '123456');
  });

  it('calls onLoginSuccess(false) on successful login without must_change_pin', async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: 'tok123',
      must_change_pin: false,
    } as any);

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), 'EMP001');
    fireEvent.changeText(getByPlaceholderText('••••'), '123456');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    expect(onLoginSuccess).toHaveBeenCalledWith(false);
  });

  it('calls onLoginSuccess(true) when must_change_pin is set', async () => {
    mockLogin.mockResolvedValueOnce({
      access_token: 'tok999',
      must_change_pin: true,
    } as any);

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), 'EMP002');
    fireEvent.changeText(getByPlaceholderText('••••'), '000001');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    expect(onLoginSuccess).toHaveBeenCalledWith(true);
  });

  it('shows error banner on login failure', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Nieprawidłowy PIN'));

    const { getByPlaceholderText, getByText, findByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), 'EMP001');
    fireEvent.changeText(getByPlaceholderText('••••'), '999999');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    expect(await findByText('Nieprawidłowy PIN')).toBeTruthy();
    expect(onLoginSuccess).not.toHaveBeenCalled();
  });

  it('shows lockout banner when error contains "zablokowane"', async () => {
    mockLogin.mockRejectedValueOnce(
      new Error('Konto zablokowane na 15 minut')
    );

    const { getByPlaceholderText, getByText, findByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), 'EMP001');
    fireEvent.changeText(getByPlaceholderText('••••'), '000000');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    expect(await findByText('Konto zablokowane')).toBeTruthy();
    expect(await findByText(/Po 5 nieudanych/)).toBeTruthy();
  });

  it('disables login button when account is locked', async () => {
    mockLogin.mockRejectedValueOnce(
      new Error('Konto zablokowane na 15 minut')
    );

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen onLoginSuccess={onLoginSuccess} />
    );
    fireEvent.changeText(getByPlaceholderText('np. 004829'), 'EMP001');
    fireEvent.changeText(getByPlaceholderText('••••'), '000000');

    await act(async () => {
      fireEvent.press(getByText('Zaloguj się'));
    });

    await waitFor(() => {
      // Po blokadzie przycisk ma prop disabled=true
      const btn = getByText('Zaloguj się').parent?.parent;
      expect(btn?.props?.accessibilityState?.disabled ?? btn?.props?.disabled).toBeTruthy();
    });
  });
});
