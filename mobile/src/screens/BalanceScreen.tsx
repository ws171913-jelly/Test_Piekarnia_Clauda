import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, fonts, radius, spacing } from '../theme';
import { userStore, UserProfile, TransactionListItem } from '../store/userStore';
import { syncAll } from '../services/sync';

interface Props {
  onGenerateCode: () => void;
  onViewHistory: () => void;
}

function formatPln(amount: number): string {
  return amount.toFixed(2).replace('.', ',') + ' PLN';
}

function formatDate(dateStr: string): string {
  const [y, m, d] = dateStr.split('-');
  return `${d}.${m}.${y}`;
}

export default function BalanceScreen({ onGenerateCode, onViewHistory }: Props) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [recentTx, setRecentTx] = useState<TransactionListItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [networkError, setNetworkError] = useState(false);

  const loadData = useCallback(async (forceSync = false) => {
    const cached = userStore.getProfile();
    const cachedTx = userStore.getTransactions();
    if (cached) {
      setProfile(cached);
      setLastSync(new Date(cached.cachedAt));
    }
    if (cachedTx) {
      setRecentTx(cachedTx.items.slice(0, 3));
    }

    if (forceSync || !cached) {
      setRefreshing(true);
      try {
        await syncAll();
        const fresh = userStore.getProfile();
        const freshTx = userStore.getTransactions();
        if (fresh) { setProfile(fresh); setLastSync(new Date(fresh.cachedAt)); }
        if (freshTx) setRecentTx(freshTx.items.slice(0, 3));
        setNetworkError(false);
      } catch {
        setNetworkError(true);
      } finally {
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const session = userStore.getSession();
  const name = session?.hrEmployeeId ?? '';

  if (!profile && !refreshing) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.flex}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => loadData(true)}
          tintColor={colors.primary}
        />
      }
    >
      {/* TopBar */}
      <View style={styles.topBar}>
        <Text style={styles.topBarName}>{name}</Text>
        <Text style={styles.topBarBrand}>BonusApp</Text>
        <Pressable
          style={styles.logoutBtn}
          onPress={() => {
            userStore.clearSession();
          }}
        >
          <Text style={styles.logoutIcon}>⎋</Text>
        </Pressable>
      </View>

      {/* Welcome */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeTitle}>Witaj, {name}</Text>
        <Text style={styles.welcomeSub}>Twój rzemieślniczy portfel korzyści.</Text>
        {networkError && (
          <Text style={styles.offlineNote}>📵 Tryb offline — dane z cache</Text>
        )}
        {lastSync && !networkError && (
          <Text style={styles.syncNote}>
            Ostatnia synchronizacja: {lastSync.toLocaleTimeString('pl-PL')}
          </Text>
        )}
      </View>

      {/* Balance card */}
      {profile && (
        <View style={styles.balanceSection}>
          <View style={styles.balanceImageCard}>
            <Image
              source={require('../assets/img/balance-card-bread.png')}
              style={styles.balanceDesignImage}
              resizeMode="cover"
            />
            <View style={styles.balanceGradient} />
          </View>
          <View style={styles.balanceOverlay}>
            <View style={styles.balanceRow}>
              <View>
                <Text style={styles.balanceLabel}>DOSTĘPNE SALDO</Text>
                <Text style={styles.balanceAmount}>
                  {profile.currentBalance.toFixed(2).replace('.', ',')}
                  <Text style={styles.balanceCurrency}> PLN</Text>
                </Text>
              </View>
              <View style={styles.discountBadge}>
                <Text style={styles.discountBadgeText}>
                  -{profile.basket.discountPct}% Rabatu
                </Text>
              </View>
            </View>
            <View style={styles.expiryRow}>
              <Text style={styles.expiryIcon}>📅</Text>
              <Text style={styles.expiryText}>
                Ważne do: {formatDate(profile.balanceExpiryDate)}
              </Text>
            </View>
            <Pressable
              style={[
                styles.generateBtn,
                profile.currentBalance <= 0 && styles.generateBtnDisabled,
              ]}
              onPress={onGenerateCode}
              disabled={profile.currentBalance <= 0}
            >
              <Text style={styles.generateBtnText}>Generuj kod rabatowy</Text>
            </Pressable>
          </View>
        </View>
      )}

      {/* Promo card — Zapraszaj znajomych */}
      <View style={styles.promoCard}>
        <View style={styles.promoImageCircle}>
          <Image
            source={require('../assets/img/coffee-circle.png')}
            style={styles.promoImage}
            resizeMode="cover"
          />
        </View>
        <View style={styles.promoContent}>
          <Text style={styles.promoTitle}>Zapraszaj znajomych</Text>
          <Text style={styles.promoDesc}>
            Poleć BonusApp kolegom z pracy i zyskaj dodatkowy rabat.
          </Text>
        </View>
      </View>

      {/* Recent transactions */}
      <View style={styles.txSection}>
        <View style={styles.txHeader}>
          <Text style={styles.txTitle}>Ostatnie transakcje</Text>
          <Pressable onPress={onViewHistory}>
            <Text style={styles.txSeeAll}>Zobacz wszystkie</Text>
          </Pressable>
        </View>

        {recentTx.length === 0 ? (
          <View style={styles.emptyTx}>
            <Text style={styles.emptyTxIcon}>🍞</Text>
            <Text style={styles.emptyTxText}>Brak transakcji</Text>
          </View>
        ) : (
          recentTx.map((tx) => (
            <View key={tx.id} style={styles.txItem}>
              <View style={styles.txIconCircle}>
                <Text style={styles.txItemIcon}>
                  {tx.type === 'ZWROT' ? '↩️' : '🛒'}
                </Text>
              </View>
              <View style={styles.txDetails}>
                <Text style={styles.txType}>
                  {tx.type === 'ZAKUP' ? 'Zakup' : 'Zwrot'}
                </Text>
                <Text style={styles.txDate}>
                  {new Date(tx.createdAt).toLocaleDateString('pl-PL')}
                </Text>
              </View>
              <Text
                style={[
                  styles.txAmount,
                  tx.type === 'ZAKUP' ? styles.txAmountDebit : styles.txAmountCredit,
                ]}
              >
                {tx.type === 'ZAKUP' ? '-' : '+'}
                {formatPln(tx.discountAmountPln)}
              </Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  container: { paddingBottom: 100, backgroundColor: colors.surface },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
    backgroundColor: colors.surface,
  },
  topBarName: { fontSize: 13, color: colors.onSurfaceVariant, fontWeight: '500' },
  topBarBrand: {
    fontFamily: fonts.headline,
    fontSize: 20,
    fontWeight: '700',
    fontStyle: 'italic',
    color: colors.primary,
  },
  logoutBtn: { padding: spacing.sm },
  logoutIcon: { fontSize: 20, color: colors.primary },

  welcomeSection: { paddingHorizontal: spacing.lg, marginBottom: spacing.lg },
  welcomeTitle: {
    fontFamily: fonts.headline,
    fontSize: 34,
    fontWeight: '600',
    fontStyle: 'italic',
    color: colors.primary,
  },
  welcomeSub: { fontSize: 14, color: colors.onSurfaceVariant, fontWeight: '500', marginTop: 2 },
  offlineNote: { fontSize: 11, color: colors.error, marginTop: spacing.xs },
  syncNote: { fontSize: 10, color: colors.onSurfaceVariant, marginTop: spacing.xs },

  balanceSection: { marginHorizontal: spacing.lg, marginBottom: spacing.lg },
  balanceImageCard: {
    height: 200,
    borderRadius: radius.xl,
    overflow: 'hidden',
    backgroundColor: colors.surfaceContainerHigh,
  },
  balanceDesignImage: { flex: 1, width: '100%' },
  balanceGradient: {
    position: 'absolute',
    bottom: 0, left: 0, right: 0, height: 100,
    backgroundColor: colors.primary,
    opacity: 0.7,
  },
  balanceOverlay: {
    marginTop: -80,
    marginHorizontal: spacing.sm,
    backgroundColor: colors.surfaceContainerHighest,
    borderRadius: radius.xl,
    padding: spacing.lg,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 40,
    elevation: 4,
    gap: spacing.sm,
  },
  balanceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  balanceLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 3,
    textTransform: 'uppercase',
  },
  balanceAmount: {
    fontFamily: fonts.headline,
    fontSize: 34,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.xs,
  },
  balanceCurrency: { fontSize: 16, fontWeight: '400' },
  discountBadge: {
    backgroundColor: colors.secondary,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  discountBadgeText: { color: colors.onSecondary, fontSize: 11, fontWeight: '700' },
  expiryRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  expiryIcon: { fontSize: 13 },
  expiryText: { fontSize: 13, color: colors.onSurfaceVariant },
  generateBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  generateBtnDisabled: { opacity: 0.4 },
  generateBtnText: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: 13,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },

  promoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: spacing.lg,
    marginBottom: spacing.lg,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.md,
    gap: spacing.md,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 16,
    elevation: 2,
  },
  promoImageCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    overflow: 'hidden',
    borderWidth: 4,
    borderColor: colors.surfaceContainerHighest,
    flexShrink: 0,
  },
  promoImage: { flex: 1, width: '100%' },
  promoContent: { flex: 1, gap: spacing.xs },
  promoTitle: {
    fontFamily: fonts.headline,
    fontSize: 17,
    fontWeight: '700',
    color: colors.onSurface,
  },
  promoDesc: { fontSize: 12, color: colors.onSurfaceVariant, lineHeight: 18 },
  txSection: { paddingHorizontal: spacing.lg },
  txHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  txTitle: {
    fontFamily: fonts.headline,
    fontSize: 22,
    fontWeight: '600',
    color: colors.onSurface,
  },
  txSeeAll: {
    color: colors.primary,
    fontWeight: '700',
    fontSize: 11,
    letterSpacing: 1,
    textTransform: 'uppercase',
    textDecorationLine: 'underline',
  },
  txItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.md,
    marginBottom: spacing.md,
    gap: spacing.md,
  },
  txIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surfaceContainerHighest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  txItemIcon: { fontSize: 20 },
  txDetails: { flex: 1 },
  txType: { fontWeight: '700', color: colors.onSurface, fontSize: 14 },
  txDate: { fontSize: 11, color: colors.onSurfaceVariant, marginTop: 2 },
  txAmount: { fontFamily: fonts.headline, fontSize: 16, fontWeight: '700' },
  txAmountDebit: { color: colors.error },
  txAmountCredit: { color: colors.primary },
  emptyTx: { alignItems: 'center', paddingVertical: spacing.xl, gap: spacing.sm },
  emptyTxIcon: { fontSize: 40 },
  emptyTxText: { color: colors.onSurfaceVariant, fontSize: 14 },
});
