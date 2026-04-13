import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, fonts, radius, spacing } from '../theme';
import { fetchTransactions, TransactionItem } from '../services/api';
import { userStore } from '../store/userStore';

interface Props {
  onBack: () => void;
}

export default function HistoryScreen({ onBack }: Props) {
  const [items, setItems] = useState<TransactionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'ALL' | 'ZAKUP' | 'ZWROT'>('ALL');
  const [hasMore, setHasMore] = useState(true);
  const [offline, setOffline] = useState(false);

  const PAGE_SIZE = 20;

  const loadPage = useCallback(
    async (p: number, currentFilter: typeof filter, reset = false) => {
      if (loading && !reset) return;
      setLoading(true);
      try {
        const typeParam = currentFilter === 'ALL' ? undefined : currentFilter;
        const data = await fetchTransactions(p, PAGE_SIZE, typeParam);
        const newItems = data.items;
        setItems((prev) => (p === 1 ? newItems : [...prev, ...newItems]));
        setTotal(data.total);
        setHasMore(p * PAGE_SIZE < data.total);
        setOffline(false);
      } catch {
        // Fallback to cache on first page
        if (p === 1) {
          const cached = userStore.getTransactions();
          if (cached) {
            const filtered =
              currentFilter === 'ALL'
                ? cached.items
                : cached.items.filter((tx) => tx.type === currentFilter);
            setItems(
              filtered.map((tx) => ({
                id: tx.id,
                type: tx.type,
                gross_amount_pln: tx.grossAmountPln,
                discount_amount_pln: tx.discountAmountPln,
                net_amount_pln: tx.netAmountPln,
                discount_pct_snapshot: tx.discountPctSnapshot,
                pos_terminal_id: tx.posTerminalId,
                created_at: tx.createdAt,
              })),
            );
            setOffline(true);
          }
        }
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [loading],
  );

  useEffect(() => {
    setPage(1);
    loadPage(1, filter, true);
  }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleRefresh() {
    setRefreshing(true);
    setPage(1);
    loadPage(1, filter, true);
  }

  function handleLoadMore() {
    if (!hasMore || loading) return;
    const nextPage = page + 1;
    setPage(nextPage);
    loadPage(nextPage, filter);
  }

  function formatPln(amount: number): string {
    return amount.toFixed(2).replace('.', ',') + ' PLN';
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString('pl-PL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function renderItem({ item }: { item: TransactionItem }) {
    const isRefund = item.type === 'ZWROT';
    return (
      <View style={styles.txItem}>
        <View style={[styles.txIconCircle, isRefund && styles.txIconRefund]}>
          <Text style={styles.txIcon}>{isRefund ? '↩️' : '🛒'}</Text>
        </View>
        <View style={styles.txBody}>
          <View style={styles.txTopRow}>
            <Text style={styles.txType}>{isRefund ? 'Zwrot' : 'Zakup'}</Text>
            <Text style={[styles.txAmount, isRefund ? styles.credit : styles.debit]}>
              {isRefund ? '+' : '-'}{formatPln(item.discount_amount_pln)}
            </Text>
          </View>
          <View style={styles.txBottomRow}>
            <Text style={styles.txDate}>{formatDate(item.created_at)}</Text>
            <Text style={styles.txDiscount}>Rabat: {item.discount_pct_snapshot}%</Text>
          </View>
          <View style={styles.txAmountRow}>
            <Text style={styles.txAmountDetail}>
              Brutto: {formatPln(item.gross_amount_pln)} → Netto: {formatPln(item.net_amount_pln)}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  function renderEmpty() {
    if (loading) return null;
    return (
      <View style={styles.emptyBox}>
        <View style={styles.emptyImageCard}>
          <Image
            source={require('../assets/img/bread-basket.png')}
            style={styles.emptyImage}
            resizeMode="cover"
          />
          <View style={styles.emptyCiszaBadge}>
            <Text style={styles.emptyCiszaText}>Cisza w piekarni</Text>
          </View>
        </View>
        <Text style={styles.emptyTitle}>Brak transakcji</Text>
        <Text style={styles.emptyDesc}>
          {filter === 'ALL'
            ? 'Nie masz jeszcze żadnych transakcji.'
            : `Brak transakcji typu: ${filter.toLowerCase()}.`}
        </Text>
      </View>
    );
  }

  function renderFooter() {
    if (!loading || refreshing) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={onBack} style={styles.backBtn}>
          <Text style={styles.backIcon}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Historia transakcji</Text>
        <View style={styles.headerAvatarCircle}>
          <Image
            source={require('../assets/img/history-avatar.png')}
            style={styles.headerAvatar}
            resizeMode="cover"
          />
        </View>
      </View>

      {/* Summary */}
      <View style={styles.summaryRow}>
        <Text style={styles.summaryText}>
          {offline ? '📵 Offline — ' : ''}Łącznie: {total}
        </Text>
      </View>

      {/* Filter chips */}
      <View style={styles.filterRow}>
        {(['ALL', 'ZAKUP', 'ZWROT'] as const).map((f) => (
          <Pressable
            key={f}
            style={[styles.filterChip, filter === f && styles.filterChipActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterChipText, filter === f && styles.filterChipTextActive]}>
              {f === 'ALL' ? 'Wszystkie' : f === 'ZAKUP' ? 'Zakupy' : 'Zwroty'}
            </Text>
          </Pressable>
        ))}
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={renderFooter}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.3}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl + spacing.md,
    paddingBottom: spacing.md,
    backgroundColor: colors.surface,
  },
  backBtn: { width: 40, alignItems: 'center' },
  headerAvatarCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: colors.outlineVariant,
  },
  headerAvatar: { flex: 1, width: '100%' },
  backIcon: { fontSize: 22, color: colors.primary },
  headerTitle: {
    fontFamily: fonts.headline,
    fontSize: 20,
    fontWeight: '600',
    fontStyle: 'italic',
    color: colors.primary,
  },
  summaryRow: { paddingHorizontal: spacing.lg, paddingBottom: spacing.sm },
  summaryText: { fontSize: 12, color: colors.onSurfaceVariant },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  filterChip: {
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    backgroundColor: colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: { fontSize: 12, fontWeight: '600', color: colors.onSurfaceVariant },
  filterChipTextActive: { color: colors.onPrimary },
  listContent: { paddingHorizontal: spacing.lg, paddingBottom: 100 },
  txItem: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.md,
    marginBottom: spacing.md,
    gap: spacing.md,
    alignItems: 'flex-start',
  },
  txIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surfaceContainerHighest,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  txIconRefund: { backgroundColor: colors.secondaryContainer },
  txIcon: { fontSize: 20 },
  txBody: { flex: 1, gap: 2 },
  txTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  txType: { fontWeight: '700', fontSize: 14, color: colors.onSurface },
  txAmount: { fontFamily: fonts.headline, fontSize: 15, fontWeight: '700' },
  debit: { color: colors.error },
  credit: { color: colors.primary },
  txBottomRow: { flexDirection: 'row', justifyContent: 'space-between' },
  txDate: { fontSize: 10, color: colors.onSurfaceVariant },
  txDiscount: { fontSize: 10, color: colors.secondary, fontWeight: '600' },
  txAmountRow: {},
  txAmountDetail: { fontSize: 10, color: colors.outline },
  emptyBox: {
    alignItems: 'center',
    paddingTop: spacing.xl,
    paddingHorizontal: spacing.lg,
    gap: spacing.lg,
  },
  emptyImageCard: {
    width: '100%',
    height: 220,
    borderRadius: radius.xl,
    overflow: 'hidden',
    backgroundColor: colors.surfaceContainerHigh,
  },
  emptyImage: { flex: 1, width: '100%' },
  emptyCiszaBadge: {
    position: 'absolute',
    bottom: spacing.md,
    right: spacing.md,
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  emptyCiszaText: {
    color: colors.onPrimary,
    fontFamily: fonts.headline,
    fontStyle: 'italic',
    fontSize: 13,
    fontWeight: '600',
  },
  emptyTitle: {
    fontFamily: fonts.headline,
    fontSize: 26,
    fontWeight: '700',
    color: colors.onSurface,
    textAlign: 'center',
  },
  emptyDesc: { fontSize: 13, color: colors.onSurfaceVariant, textAlign: 'center', lineHeight: 20 },
  footerLoader: { paddingVertical: spacing.xl, alignItems: 'center' },
});
