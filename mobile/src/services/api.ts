import axios, { AxiosInstance, AxiosError } from 'axios';
import { userStore } from '../store/userStore';

const BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = userStore.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function extractDetail(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    return String(err.response.data.detail);
  }
  if (err instanceof Error) return err.message;
  return 'Nieznany błąd';
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  must_change_pin: boolean;
}

export async function login(hrEmployeeId: string, pin: string): Promise<LoginResponse> {
  try {
    const { data } = await client.post<LoginResponse>('/api/v1/auth/login', {
      hr_employee_id: hrEmployeeId,
      pin,
    });
    return data;
  } catch (err) {
    throw new Error(extractDetail(err));
  }
}

export interface ChangePinResponse {
  access_token: string;
}

export async function changePin(newPin: string, confirmPin: string): Promise<ChangePinResponse> {
  try {
    const { data } = await client.post<ChangePinResponse>('/api/v1/auth/change-pin', {
      new_pin: newPin,
      confirm_pin: confirmPin,
    });
    return data;
  } catch (err) {
    throw new Error(extractDetail(err));
  }
}

// ── Codes ─────────────────────────────────────────────────────────────────────

export interface GenerateCodeResponse {
  code: string;
  expires_at: string;
  code_id: string;
}

export async function generateCode(): Promise<GenerateCodeResponse> {
  try {
    const { data } = await client.post<GenerateCodeResponse>('/api/v1/codes');
    return data;
  } catch (err) {
    throw new Error(extractDetail(err));
  }
}

// ── Users ─────────────────────────────────────────────────────────────────────

export interface UserProfileResponse {
  hr_employee_id: string;
  current_balance: number;
  balance_expiry_date: string;
  basket: {
    id: string;
    name: string;
    discount_pct: number;
    monthly_limit_pln: number | null;
  };
  location_id: string;
  must_change_pin: boolean;
}

export async function fetchProfile(): Promise<UserProfileResponse> {
  try {
    const { data } = await client.get<UserProfileResponse>('/api/v1/users/me');
    return data;
  } catch (err) {
    throw new Error(extractDetail(err));
  }
}

export interface TransactionItem {
  id: string;
  type: string;
  gross_amount_pln: number;
  discount_amount_pln: number;
  net_amount_pln: number;
  discount_pct_snapshot: number;
  pos_terminal_id: string;
  created_at: string;
}

export interface TransactionHistoryResponse {
  items: TransactionItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function fetchTransactions(
  page = 1,
  pageSize = 20,
  type?: string,
): Promise<TransactionHistoryResponse> {
  try {
    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (type) params.type = type;
    const { data } = await client.get<TransactionHistoryResponse>('/api/v1/users/me/transactions', {
      params,
    });
    return data;
  } catch (err) {
    throw new Error(extractDetail(err));
  }
}
