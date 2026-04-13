import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, fonts, radius, spacing } from '../theme';
import { generateCode } from '../services/api';
import { userStore } from '../store/userStore';

const CODE_TTL_SECONDS = 15 * 60; // 15 min

interface Props {
  onBack: () => void;
}

type ScreenState = 'loading' | 'active' | 'no_balance' | 'cooldown' | 'error';

export default function CodeDisplayScreen({ onBack }: Props) {
  const [state, setState] = useState<ScreenState>('loading');
  const [code, setCode] = useState<string>('');
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(CODE_TTL_SECONDS);
  const [errorMsg, setErrorMsg] = useState('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const progressAnim = useRef(new Animated.Value(1)).current;

  const profile = userStore.getProfile();
  const balance = profile?.currentBalance ?? 0;
  const discountPct = profile?.basket.discountPct ?? 0;

  const loadCode = useCallback(async () => {
    setState('loading');
    try {
      const result = await generateCode();
      setCode(result.code);
      const exp = new Date(result.expires_at);
      setExpiresAt(exp);
      const remaining = Math.max(0, Math.floor((exp.getTime() - Date.now()) / 1000));
      setSecondsLeft(remaining);
      setState('active');

      progressAnim.setValue(1);
      Animated.timing(progressAnim, {
        toValue: 0,
        duration: remaining * 1000,
        useNativeDriver: false,
      }).start();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Błąd generowania kodu';
      if (msg.toLowerCase().includes('saldo') || msg.toLowerCase().includes('brak')) {
        setState('no_balance');
      } else if (msg.toLowerCase().includes('karencja') || msg.toLowerCase().includes('poczekaj')) {
        setErrorMsg(msg);
        setState('cooldown');
      } else {
        setErrorMsg(msg);
        setState('error');
      }
    }
  }, [progressAnim]);

  useEffect(() => {
    loadCode();
  }, [loadCode]);

  useEffect(() => {
    if (state !== 'active') return;
    intervalRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(intervalRef.current!);
          setState('error');
          setErrorMsg('Kod wygasł');
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [state]);

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  function formatCode(raw: string): string {
    return raw.length === 6 ? `${raw.slice(0, 3)} ${raw.slice(3)}` : raw;
  }

  function formatPln(amount: number): string {
    return amount.toFixed(2).replace('.', ',') + ' PLN';
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={onBack} style={styles.backBtn}>
          <Text style={styles.backIcon}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Kod rabatowy</Text>
        <View style={styles.backBtn} />
      </View>

      {/* Content */}
      <View style={styles.content}>
        {state === 'loading' && (
          <View style={styles.centerBox}>
            <ActivityIndicator color={colors.primary} size="large" />
            <Text style={styles.loadingText}>Generowanie kodu…</Text>
          </View>
        )}

        {state === 'no_balance' && (
          <View style={styles.statusCard}>
            {/* Bowl image with stacked paper effect */}
            <View style={styles.noBalanceImageWrapper}>
              <View style={styles.noBalancePaperBack} />
              <View style={styles.noBalancePaperFront} />
              <View style={styles.noBalanceImageContainer}>
                <Image
                  source={require('../assets/img/code-no-balance-bowl.png')}
                  style={styles.noBalanceImage}
                  resizeMode="cover"
                />
              </View>
              <View style={styles.noBalanceBadge}>
                <Text style={styles.noBalanceBadgeText}>Wymagana wpłata</Text>
              </View>
            </View>
            <Text style={styles.statusTitle}>Brak salda</Text>
            <Text style={styles.statusDesc}>
              Twoje saldo wynosi 0,00 PLN. Doładowanie odbywa się automatycznie co miesiąc.
              Skontaktuj się z HR jeśli masz pytania.
            </Text>
            <View style={styles.infoGrid}>
              <View style={styles.infoTile}>
                <Text style={styles.infoLabel}>SALDO</Text>
                <Text style={styles.infoValue}>{formatPln(balance)}</Text>
              </View>
              <View style={styles.infoTile}>
                <Text style={styles.infoLabel}>RABAT</Text>
                <Text style={styles.infoValue}>{discountPct}%</Text>
              </View>
            </View>
            <Pressable style={styles.backBtnLarge} onPress={onBack}>
              <Text style={styles.backBtnText}>Wróć do dashboardu</Text>
            </Pressable>
          </View>
        )}

        {state === 'cooldown' && (
          <View style={styles.statusCard}>
            <View style={styles.statusIconCircle}>
              <Text style={styles.statusIcon}>⏳</Text>
            </View>
            <Text style={styles.statusTitle}>Karencja aktywna</Text>
            <Text style={styles.statusDesc}>{errorMsg}</Text>
            <Pressable style={styles.backBtnLarge} onPress={onBack}>
              <Text style={styles.backBtnText}>Wróć do dashboardu</Text>
            </Pressable>
          </View>
        )}

        {(state === 'error') && errorMsg !== '' && (
          <View style={styles.statusCard}>
            <View style={[styles.statusIconCircle, styles.errorCircle]}>
              <Text style={styles.statusIcon}>⚠️</Text>
            </View>
            <Text style={styles.statusTitle}>{errorMsg}</Text>
            <Pressable style={styles.retryBtn} onPress={loadCode}>
              <Text style={styles.retryBtnText}>Spróbuj ponownie</Text>
            </Pressable>
            <Pressable style={styles.backBtnLarge} onPress={onBack}>
              <Text style={styles.backBtnText}>Wróć</Text>
            </Pressable>
          </View>
        )}

        {state === 'active' && (
          <View style={styles.activeCard}>
            {/* Texture banner */}
            <View style={styles.textureBanner}>
              <Image
                source={require('../assets/img/code-card-texture.png')}
                style={styles.textureImage}
                resizeMode="cover"
              />
              <View style={styles.textureDimOverlay} />
            </View>

            {/* Code display */}
            <View style={styles.codeSection}>
              <View style={styles.codeHeaderRow}>
                <Text style={styles.codeStatusDot}>●</Text>
                <Text style={styles.codeStatusText}>KOD AKTYWNY</Text>
              </View>
              <Text style={styles.codeLabel}>TWÓJ UNIKALNY KOD</Text>
              <Text style={styles.codeValue} selectable>
                {formatCode(code)}
              </Text>

              {/* TTL bar */}
              <View style={styles.ttlRow}>
                <View style={styles.progressBar}>
                  <Animated.View
                    style={[
                      styles.progressFill,
                      {
                        width: progressAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: ['0%', '100%'],
                        }),
                      },
                    ]}
                  />
                </View>
                <View style={styles.ttlLabelRow}>
                  <Text style={styles.ttlLeft}>
                    Ważny do:{' '}
                    <Text style={styles.ttlTime}>
                      {expiresAt?.toLocaleTimeString('pl-PL', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </Text>
                  </Text>
                  <Text style={styles.ttlCountdown}>Wygaśnie za {formatTime(secondsLeft)}</Text>
                </View>
              </View>
            </View>

            {/* Stats */}
            <View style={styles.statsGrid}>
              <View style={styles.statTile}>
                <Text style={styles.statLabel}>RABAT</Text>
                <Text style={styles.statValue}>{discountPct}%</Text>
              </View>
              <View style={styles.statTile}>
                <Text style={styles.statLabel}>SALDO</Text>
                <Text style={styles.statValue}>{formatPln(balance)}</Text>
              </View>
            </View>

            {/* Hint */}
            <Text style={styles.hint}>
              Pokaż ten kod sprzedawcy przy kasie przed dokonaniem płatności, aby naliczyć zniżkę.
            </Text>
          </View>
        )}
      </View>
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
  backIcon: { fontSize: 22, color: colors.primary },
  headerTitle: {
    fontFamily: fonts.headline,
    fontSize: 20,
    fontWeight: '600',
    fontStyle: 'italic',
    color: colors.primary,
  },
  content: { flex: 1, paddingHorizontal: spacing.lg, paddingTop: spacing.xl },
  centerBox: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  loadingText: { color: colors.onSurfaceVariant, fontSize: 14 },

  statusCard: {
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    gap: spacing.lg,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.06,
    shadowRadius: 24,
    elevation: 3,
  },
  statusIconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.surfaceContainerHigh,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorCircle: { backgroundColor: colors.errorContainer },
  statusIcon: { fontSize: 36 },
  statusTitle: {
    fontFamily: fonts.headline,
    fontSize: 24,
    fontWeight: '700',
    color: colors.primary,
    textAlign: 'center',
  },
  statusDesc: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    lineHeight: 20,
  },
  infoGrid: { flexDirection: 'row', gap: spacing.md, width: '100%' },
  infoTile: {
    flex: 1,
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
  },
  infoLabel: { fontSize: 9, fontWeight: '700', color: colors.primary, letterSpacing: 2 },
  infoValue: { fontSize: 20, fontWeight: '700', color: colors.onSurface, marginTop: spacing.xs },
  noBalanceImageWrapper: {
    position: 'relative',
    width: '100%',
    alignItems: 'center',
    paddingBottom: spacing.xl,
  },
  noBalancePaperBack: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: spacing.xl,
    backgroundColor: colors.surfaceContainerHigh,
    borderRadius: radius.xl,
    transform: [{ rotate: '3deg' }, { scale: 0.95 }],
    opacity: 0.5,
  },
  noBalancePaperFront: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: spacing.xl,
    backgroundColor: colors.surfaceContainerHighest,
    borderRadius: radius.xl,
    transform: [{ rotate: '-2deg' }],
  },
  noBalanceImageContainer: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: radius.xl,
    overflow: 'hidden',
  },
  noBalanceImage: { flex: 1, width: '100%' },
  noBalanceBadge: {
    position: 'absolute',
    bottom: 0,
    right: spacing.md,
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    transform: [{ rotate: '-1deg' }],
  },
  noBalanceBadgeText: {
    color: colors.onPrimary,
    fontFamily: fonts.headline,
    fontStyle: 'italic',
    fontSize: 13,
    fontWeight: '600',
  },
  backBtnLarge: {
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    width: '100%',
  },
  backBtnText: { color: colors.primary, fontWeight: '700', fontSize: 14 },
  retryBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    width: '100%',
  },
  retryBtnText: { color: colors.onPrimary, fontWeight: '700', fontSize: 14 },

  activeCard: {
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    overflow: 'hidden',
    gap: spacing.lg,
    paddingBottom: spacing.xl,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 40,
    elevation: 5,
  },
  textureBanner: {
    height: 140,
    overflow: 'hidden',
  },
  textureImage: { flex: 1, width: '100%' },
  textureDimOverlay: {
    position: 'absolute',
    bottom: 0, left: 0, right: 0, height: 60,
    backgroundColor: colors.surfaceContainerLow,
    opacity: 0.6,
  },
  codeSection: { gap: spacing.md, alignItems: 'center', paddingHorizontal: spacing.xl },
  codeHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  codeStatusDot: { color: '#4caf50', fontSize: 14 },
  codeStatusText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.onSurfaceVariant,
    letterSpacing: 3,
  },
  codeLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.outline,
    letterSpacing: 3,
    textTransform: 'uppercase',
  },
  codeValue: {
    fontFamily: 'monospace',
    fontSize: 44,
    fontWeight: '700',
    color: colors.onSurface,
    letterSpacing: 8,
    textAlign: 'center',
    paddingVertical: spacing.md,
  },
  ttlRow: { width: '100%', gap: spacing.sm },
  progressBar: {
    height: 6,
    backgroundColor: colors.surfaceContainer,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: { height: '100%', backgroundColor: colors.primary, borderRadius: 3 },
  ttlLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ttlLeft: { fontSize: 10, color: colors.outline },
  ttlTime: { fontWeight: '700', color: colors.onSurface },
  ttlCountdown: { fontSize: 11, fontWeight: '700', fontStyle: 'italic', color: colors.primary },
  statsGrid: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.xl },
  statTile: {
    flex: 1,
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
    gap: spacing.xs,
  },
  statLabel: { fontSize: 9, fontWeight: '700', color: colors.primary, letterSpacing: 2 },
  statValue: { fontSize: 18, fontWeight: '700', color: colors.onSurface },
  hint: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 18,
    paddingHorizontal: spacing.xl,
  },
});
