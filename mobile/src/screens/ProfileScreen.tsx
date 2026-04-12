import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, radius, spacing } from '../theme';
import { userStore } from '../store/userStore';

interface Props {
  onChangePin: () => void;
  onLogout: () => void;
}

export default function ProfileScreen({ onChangePin, onLogout }: Props) {
  const session = userStore.getSession();
  const profile = userStore.getProfile();
  const employeeId = session?.hrEmployeeId ?? '';
  const basketName = profile?.basket.name ?? '';
  const discountPct = profile?.basket.discountPct ?? 0;

  function handleLogout() {
    userStore.clearSession();
    onLogout();
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <Text style={styles.topBarBrand}>BonusApp</Text>
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarInitial}>
            {employeeId.charAt(0).toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.profileAvatarWrap}>
          <View style={styles.profileAvatarCircle}>
            <Text style={styles.profileAvatarText}>
              {employeeId.charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.editBadge}>
            <Text style={styles.editBadgeIcon}>✏</Text>
          </View>
        </View>
        <Text style={styles.profileName}>{employeeId}</Text>
        <Text style={styles.profileId}>{employeeId}</Text>
      </View>

      {/* Personal Info Card */}
      <View style={styles.infoCard}>
        <View style={styles.infoCardDecor} />
        <Text style={styles.sectionLabel}>Dane pracownicze</Text>
        <View style={styles.infoFieldGroup}>
          <View style={styles.infoField}>
            <Text style={styles.infoFieldLabel}>KOSZYK</Text>
            <Text style={styles.infoFieldValue}>{basketName || '—'}</Text>
          </View>
          <View style={styles.infoField}>
            <Text style={styles.infoFieldLabel}>RABAT</Text>
            <Text style={styles.infoFieldValue}>{discountPct}%</Text>
          </View>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionsSection}>
        <Text style={styles.sectionLabel}>Ustawienia i pomoc</Text>

        <Pressable style={styles.actionItem} onPress={onChangePin}>
          <View style={styles.actionIconWrap}>
            <Text style={styles.actionIcon}>🔑</Text>
          </View>
          <Text style={styles.actionLabel}>Zmień kod PIN</Text>
          <Text style={styles.actionChevron}>›</Text>
        </Pressable>

        <Pressable style={styles.actionItem}>
          <View style={styles.actionIconWrap}>
            <Text style={styles.actionIcon}>📄</Text>
          </View>
          <Text style={styles.actionLabel}>Regulamin</Text>
          <Text style={styles.actionChevron}>›</Text>
        </Pressable>

        <Pressable style={styles.actionItem}>
          <View style={styles.actionIconWrap}>
            <Text style={styles.actionIcon}>🔒</Text>
          </View>
          <Text style={styles.actionLabel}>Polityka prywatności</Text>
          <Text style={styles.actionChevron}>›</Text>
        </Pressable>
      </View>

      {/* Logout */}
      <View style={styles.logoutSection}>
        <Pressable style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutIcon}>⎋</Text>
          <Text style={styles.logoutText}>Wyloguj się</Text>
        </Pressable>
        <Text style={styles.versionText}>BONUSAPP V2.4.1</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  container: { paddingBottom: 120, backgroundColor: colors.surface },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
  },
  topBarBrand: {
    fontFamily: 'serif',
    fontSize: 22,
    fontWeight: '700',
    fontStyle: 'italic',
    color: colors.primary,
  },
  avatarCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.outlineVariant,
  },
  avatarInitial: { fontSize: 16, fontWeight: '700', color: colors.onPrimary },

  profileHeader: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
    gap: spacing.xs,
  },
  profileAvatarWrap: { position: 'relative', marginBottom: spacing.sm },
  profileAvatarCircle: {
    width: 112,
    height: 112,
    borderRadius: 56,
    backgroundColor: colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 4,
    borderColor: colors.surfaceContainer,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 6,
  },
  profileAvatarText: { fontSize: 42, fontWeight: '700', color: colors.onPrimary },
  editBadge: {
    position: 'absolute',
    bottom: 4,
    right: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: colors.surface,
  },
  editBadgeIcon: { fontSize: 14, color: colors.onPrimary },
  profileName: {
    fontFamily: 'serif',
    fontSize: 28,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.xs,
  },
  profileId: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 3,
    textTransform: 'uppercase',
  },

  infoCard: {
    marginHorizontal: spacing.lg,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.xl,
    marginBottom: spacing.lg,
    overflow: 'hidden',
  },
  infoCardDecor: {
    position: 'absolute',
    top: -40,
    right: -40,
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.primary,
    opacity: 0.05,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 2,
    textTransform: 'uppercase',
    marginBottom: spacing.lg,
  },
  infoFieldGroup: { gap: spacing.lg },
  infoField: { gap: spacing.xs },
  infoFieldLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.onSurfaceVariant,
    letterSpacing: 3,
    textTransform: 'uppercase',
  },
  infoFieldValue: {
    fontFamily: 'serif',
    fontSize: 18,
    fontWeight: '600',
    color: colors.onSurface,
  },

  actionsSection: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.lg,
    gap: spacing.xs,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.xl,
    padding: spacing.lg,
    gap: spacing.md,
    marginTop: spacing.xs,
  },
  actionIconWrap: {
    width: 40,
    height: 40,
    borderRadius: radius.lg,
    backgroundColor: colors.surfaceContainerHighest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIcon: { fontSize: 20 },
  actionLabel: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.onSurface },
  actionChevron: { fontSize: 22, color: colors.outlineVariant, fontWeight: '300' },

  logoutSection: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.xl,
    alignItems: 'center',
    gap: spacing.lg,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    backgroundColor: colors.error,
    borderRadius: radius.xl,
    paddingVertical: spacing.md + 2,
    width: '100%',
  },
  logoutIcon: { fontSize: 20, color: colors.onPrimary },
  logoutText: { color: colors.onPrimary, fontWeight: '700', fontSize: 15 },
  versionText: {
    fontSize: 9,
    color: colors.outlineVariant,
    letterSpacing: 4,
    textTransform: 'uppercase',
  },
});
