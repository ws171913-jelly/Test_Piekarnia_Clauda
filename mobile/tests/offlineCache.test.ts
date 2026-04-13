/**
 * T041 — Test cache offline: dane wyświetlają się bez sieci przez 24h.
 *
 * Weryfikuje logikę userStore (MMKV) niezależnie od sieci:
 * - saveProfile / getProfile — dane dostępne do 24h
 * - saveTransactions / getTransactions — dane dostępne do 24h
 * - wygaśnięcie cache po 24h
 * - clearSession usuwa wszystkie dane
 * - getLastSyncTime zwraca czas ostatniego zapisu
 */

// Mock MMKV jest ładowany automatycznie z __mocks__/react-native-mmkv.ts
jest.mock('react-native-mmkv');

import { MMKV } from 'react-native-mmkv';
import { userStore, UserProfile, TransactionHistoryLite } from '../src/store/userStore';

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

function makeProfile(overrides: Partial<UserProfile> = {}): Omit<UserProfile, 'cachedAt'> {
  return {
    hrEmployeeId: 'EMP_OFFLINE_001',
    currentBalance: 350.0,
    balanceExpiryDate: '2026-12-31',
    basket: {
      id: 'basket-1',
      name: 'Koszyk Standard',
      discountPct: 20,
      monthlyLimitPln: null,
    },
    locationId: 'LOC_001',
    mustChangePin: false,
    ...overrides,
  };
}

function makeTxHistory(): Omit<TransactionHistoryLite, 'cachedAt'> {
  return {
    items: [
      {
        id: 'tx-001',
        type: 'ZAKUP',
        grossAmountPln: 50.0,
        discountAmountPln: 10.0,
        netAmountPln: 40.0,
        discountPctSnapshot: 20,
        posTerminalId: 'terminal-dev',
        createdAt: '2026-04-10T12:00:00Z',
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  };
}

describe('userStore — offline cache', () => {
  beforeEach(() => {
    // Czyść mock storage przed każdym testem
    const instance = new MMKV();
    instance.clearAll();
  });

  // --- profil ---

  it('getProfile returns null when nothing cached', () => {
    expect(userStore.getProfile()).toBeNull();
  });

  it('saveProfile + getProfile returns stored data within 24h', () => {
    const profile = makeProfile();
    userStore.saveProfile(profile);

    const result = userStore.getProfile();
    expect(result).not.toBeNull();
    expect(result?.hrEmployeeId).toBe('EMP_OFFLINE_001');
    expect(result?.currentBalance).toBe(350.0);
    expect(result?.basket.discountPct).toBe(20);
  });

  it('getProfile returns null after cache TTL of 24h', () => {
    const profile = makeProfile();
    userStore.saveProfile(profile);

    // Przesuń czas o 24h + 1s
    const realNow = Date.now;
    Date.now = jest.fn(() => realNow() + TWENTY_FOUR_HOURS_MS + 1000);

    const result = userStore.getProfile();
    expect(result).toBeNull();

    Date.now = realNow;
  });

  it('getProfile returns data when exactly 24h have not yet passed', () => {
    const profile = makeProfile();
    userStore.saveProfile(profile);

    const realNow = Date.now;
    // 23h 59min — wciąż w oknie
    Date.now = jest.fn(() => realNow() + TWENTY_FOUR_HOURS_MS - 60_000);

    const result = userStore.getProfile();
    expect(result).not.toBeNull();

    Date.now = realNow;
  });

  // --- transakcje ---

  it('getTransactions returns null when nothing cached', () => {
    expect(userStore.getTransactions()).toBeNull();
  });

  it('saveTransactions + getTransactions returns stored data within 24h', () => {
    const history = makeTxHistory();
    userStore.saveTransactions(history);

    const result = userStore.getTransactions();
    expect(result).not.toBeNull();
    expect(result?.items).toHaveLength(1);
    expect(result?.items[0].type).toBe('ZAKUP');
    expect(result?.total).toBe(1);
  });

  it('getTransactions returns null after 24h TTL', () => {
    userStore.saveTransactions(makeTxHistory());

    const realNow = Date.now;
    Date.now = jest.fn(() => realNow() + TWENTY_FOUR_HOURS_MS + 1000);

    expect(userStore.getTransactions()).toBeNull();

    Date.now = realNow;
  });

  // --- sesja ---

  it('saveSession + getSession round-trips correctly', () => {
    userStore.saveSession({
      accessToken: 'jwt-abc-123',
      hrEmployeeId: 'EMP_SESSION_001',
      mustChangePin: false,
      cachedAt: Date.now(),
    });

    const session = userStore.getSession();
    expect(session?.accessToken).toBe('jwt-abc-123');
    expect(session?.hrEmployeeId).toBe('EMP_SESSION_001');
  });

  it('getToken returns accessToken from session', () => {
    userStore.saveSession({
      accessToken: 'tok-xyz',
      hrEmployeeId: 'EMP_001',
      mustChangePin: false,
      cachedAt: Date.now(),
    });
    expect(userStore.getToken()).toBe('tok-xyz');
  });

  it('getToken returns null when no session', () => {
    expect(userStore.getToken()).toBeNull();
  });

  // --- clearSession ---

  it('clearSession removes all cached data', () => {
    userStore.saveSession({
      accessToken: 'tok',
      hrEmployeeId: 'EMP',
      mustChangePin: false,
      cachedAt: Date.now(),
    });
    userStore.saveProfile(makeProfile());
    userStore.saveTransactions(makeTxHistory());

    userStore.clearSession();

    expect(userStore.getSession()).toBeNull();
    expect(userStore.getProfile()).toBeNull();
    expect(userStore.getTransactions()).toBeNull();
  });

  // --- getLastSyncTime ---

  it('getLastSyncTime returns null when no profile cached', () => {
    expect(userStore.getLastSyncTime()).toBeNull();
  });

  it('getLastSyncTime returns Date close to save time', () => {
    const before = Date.now();
    userStore.saveProfile(makeProfile());
    const after = Date.now();

    const syncTime = userStore.getLastSyncTime();
    expect(syncTime).not.toBeNull();
    const ts = syncTime!.getTime();
    expect(ts).toBeGreaterThanOrEqual(before);
    expect(ts).toBeLessThanOrEqual(after + 10); // margines 10ms
  });
});
