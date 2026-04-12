import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'bonusapp-store' });

export interface UserSession {
  accessToken: string;
  hrEmployeeId: string;
  mustChangePin: boolean;
  cachedAt: number;
}

export interface BasketInfo {
  id: string;
  name: string;
  discountPct: number;
  monthlyLimitPln: number | null;
}

export interface UserProfile {
  hrEmployeeId: string;
  currentBalance: number;
  balanceExpiryDate: string;
  basket: BasketInfo;
  locationId: string;
  mustChangePin: boolean;
  cachedAt: number;
}

export interface TransactionListItem {
  id: string;
  type: string;
  grossAmountPln: number;
  discountAmountPln: number;
  netAmountPln: number;
  discountPctSnapshot: number;
  posTerminalId: string;
  createdAt: string;
}

export interface TransactionHistoryLite {
  items: TransactionListItem[];
  total: number;
  page: number;
  pageSize: number;
  cachedAt: number;
}

const KEYS = {
  SESSION: 'session',
  PROFILE: 'profile',
  TRANSACTIONS: 'transactions',
} as const;

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h

export const userStore = {
  saveSession(session: UserSession): void {
    storage.set(KEYS.SESSION, JSON.stringify(session));
  },

  getSession(): UserSession | null {
    const raw = storage.getString(KEYS.SESSION);
    return raw ? (JSON.parse(raw) as UserSession) : null;
  },

  clearSession(): void {
    storage.delete(KEYS.SESSION);
    storage.delete(KEYS.PROFILE);
    storage.delete(KEYS.TRANSACTIONS);
  },

  getToken(): string | null {
    return this.getSession()?.accessToken ?? null;
  },

  saveProfile(profile: Omit<UserProfile, 'cachedAt'>): void {
    const data: UserProfile = { ...profile, cachedAt: Date.now() };
    storage.set(KEYS.PROFILE, JSON.stringify(data));
  },

  getProfile(): UserProfile | null {
    const raw = storage.getString(KEYS.PROFILE);
    if (!raw) return null;
    const data = JSON.parse(raw) as UserProfile;
    if (Date.now() - data.cachedAt > CACHE_TTL_MS) return null;
    return data;
  },

  saveTransactions(data: Omit<TransactionHistoryLite, 'cachedAt'>): void {
    const cache: TransactionHistoryLite = { ...data, cachedAt: Date.now() };
    storage.set(KEYS.TRANSACTIONS, JSON.stringify(cache));
  },

  getTransactions(): TransactionHistoryLite | null {
    const raw = storage.getString(KEYS.TRANSACTIONS);
    if (!raw) return null;
    const data = JSON.parse(raw) as TransactionHistoryLite;
    if (Date.now() - data.cachedAt > CACHE_TTL_MS) return null;
    return data;
  },

  getLastSyncTime(): Date | null {
    const profile = this.getProfile();
    if (!profile) return null;
    return new Date(profile.cachedAt);
  },
};
