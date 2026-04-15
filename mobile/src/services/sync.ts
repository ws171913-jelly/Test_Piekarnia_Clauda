import { fetchProfile, fetchTransactions } from './api';
import { userStore } from '../store/userStore';

export type SyncStatus = 'idle' | 'syncing' | 'success' | 'error';

let _onStatusChange: ((status: SyncStatus) => void) | null = null;

export function setSyncListener(cb: (status: SyncStatus) => void): void {
  _onStatusChange = cb;
}

function emit(status: SyncStatus): void {
  _onStatusChange?.(status);
}

export async function syncAll(): Promise<boolean> {
  emit('syncing');
  try {
    const [profile, transactions] = await Promise.all([
      fetchProfile(),
      fetchTransactions(1, 20),
    ]);

    userStore.saveProfile({
      hrEmployeeId: profile.hr_employee_id,
      currentBalance: profile.current_balance,
      balanceExpiryDate: profile.balance_expiry_date,
      basket: {
        id: profile.basket.id,
        name: profile.basket.name,
        discountPct: profile.basket.discount_pct,
        monthlyLimitPln: profile.basket.monthly_limit_pln,
      },
      locationId: profile.location_id,
      mustChangePin: profile.must_change_pin,
    });

    userStore.saveTransactions({
      items: transactions.items.map((tx) => ({
        id: tx.id,
        type: tx.type,
        grossAmountPln: tx.gross_amount_pln,
        discountAmountPln: tx.discount_amount_pln,
        netAmountPln: tx.net_amount_pln,
        discountPctSnapshot: tx.discount_pct_snapshot,
        posTerminalId: tx.pos_terminal_id,
        createdAt: tx.created_at,
      })),
      total: transactions.total,
      page: transactions.page,
      pageSize: transactions.page_size,
    });

    emit('success');
    return true;
  } catch {
    emit('error');
    return false;
  }
}
