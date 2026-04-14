import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { colors, fonts, radius, spacing } from '../theme';
import { login } from '../services/api';
import { userStore } from '../store/userStore';

interface Props {
  onLoginSuccess: (mustChangePin: boolean) => void;
}

export default function LoginScreen({ onLoginSuccess }: Props) {
  const [employeeId, setEmployeeId] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLocked, setIsLocked] = useState(false);

  async function handleLogin() {
    if (!employeeId.trim() || !pin.trim()) {
      setError('Wprowadź numer pracownika i PIN');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await login(employeeId.trim(), pin.trim());
      userStore.saveSession({
        accessToken: result.access_token,
        hrEmployeeId: employeeId.trim(),
        mustChangePin: result.must_change_pin,
        cachedAt: Date.now(),
      });
      onLoginSuccess(result.must_change_pin);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Błąd logowania';
      setError(msg);
      if (msg.toLowerCase().includes('zablokowane')) {
        setIsLocked(true);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* Brand header */}
        <View style={styles.header}>
          <View style={styles.imageCard}>
            <Image
              source={require('../assets/img/hero-bakery.png')}
              style={styles.designImage}
              resizeMode="cover"
            />
            <View style={styles.imageGradient} />
          </View>
          <View style={styles.brandSection}>
            <Text style={styles.brandTitle}>BonusApp</Text>
            <Text style={styles.brandSubtitle}>TWÓJ RZEMIEŚLNICZY SYSTEM PREMIOWY</Text>
          </View>
        </View>

        {/* Login form */}
        <View style={styles.formCard}>
          {/* Error/lock banner */}
          {isLocked && (
            <View style={styles.lockBanner}>
              <View style={styles.lockIconCircle}>
                <Text style={styles.lockIcon}>🔒</Text>
              </View>
              <View style={styles.lockTextBox}>
                <Text style={styles.lockTitle}>Konto zablokowane na 15 minut</Text>
                <Text style={styles.lockDesc}>
                  Po 5 nieudanych próbach konto zostało zablokowane na 15 minut.
                </Text>
              </View>
            </View>
          )}

          {error && !isLocked && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorIcon}>⚠</Text>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Employee ID field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>NUMER PRACOWNIKA</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={employeeId}
                onChangeText={setEmployeeId}
                placeholder="np. 004829"
                placeholderTextColor={colors.outlineVariant}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="default"
                editable={!loading}
              />
              <Text style={[styles.inputIcon, styles.iconBadge]}>🪪</Text>
            </View>
            <View style={styles.inputUnderline} />
          </View>

          {/* PIN field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>KOD PIN</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.pinInput]}
                value={pin}
                onChangeText={setPin}
                placeholder="••••"
                placeholderTextColor={colors.outlineVariant}
                secureTextEntry
                maxLength={6}
                keyboardType="number-pad"
                editable={!loading}
              />
              <Text style={styles.inputIcon}>🔒</Text>
            </View>
            <View style={styles.inputUnderline} />
          </View>

          {/* Submit button */}
          <Pressable
            style={[styles.loginBtn, (loading || isLocked) && styles.loginBtnDisabled]}
            onPress={handleLogin}
            disabled={loading || isLocked}
          >
            {loading ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : (
              <>
                <Text style={styles.loginBtnText}>Zaloguj się</Text>
                <Text style={styles.loginBtnArrow}> →</Text>
              </>
            )}
          </Pressable>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Pressable
            onPress={() =>
              Alert.alert(
                'Nie pamiętasz danych?',
                'Skontaktuj się z działem HR — zresetują Twój PIN i wyślą nowe dane logowania.',
                [{ text: 'OK' }],
              )
            }
          >
            <Text style={styles.footerLink}>Nie pamiętasz danych?</Text>
          </Pressable>
          <Text style={styles.footerVersion}>· · · Wersja 2.4.0 Artisan · · ·</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  container: {
    flexGrow: 1,
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
    gap: spacing.xl,
    backgroundColor: colors.surface,
  },
  header: { width: '100%', alignItems: 'center' },
  imageCard: {
    width: '100%',
    height: 180,
    borderRadius: radius.xl,
    overflow: 'hidden',
    backgroundColor: colors.surfaceContainerHigh,
  },
  designImage: {
    flex: 1,
    width: '100%',
  },
  imageGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 80,
    backgroundColor: colors.surface,
    opacity: 0.6,
  },
  brandSection: { alignItems: 'center', marginTop: -spacing.xxl },
  brandTitle: {
    fontFamily: fonts.headline,
    fontSize: 42,
    fontWeight: '700',
    fontStyle: 'italic',
    color: colors.primary,
    letterSpacing: -1,
  },
  brandSubtitle: {
    fontSize: 10,
    letterSpacing: 3,
    color: colors.onSurfaceVariant,
    fontWeight: '600',
    marginTop: spacing.xs,
  },
  formCard: {
    width: '100%',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.xl,
    gap: spacing.lg,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 40,
    elevation: 4,
  },
  lockBanner: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.lg,
    gap: spacing.md,
    alignItems: 'flex-start',
    borderWidth: 1,
    borderColor: colors.error + '1a',
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 3,
  },
  lockIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.error + '1a',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  lockIcon: { fontSize: 18 },
  lockTextBox: { flex: 1 },
  lockTitle: {
    color: colors.onSurface,
    fontWeight: '700',
    fontSize: 14,
  },
  lockDesc: {
    color: colors.onSurfaceVariant,
    fontSize: 12,
    marginTop: 2,
    lineHeight: 18,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.errorContainer + '66',
    borderRadius: radius.md,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: colors.error,
  },
  errorIcon: { fontSize: 16, color: colors.error },
  errorText: {
    flex: 1,
    color: colors.error,
    fontSize: 13,
    fontWeight: '600',
  },
  fieldGroup: { gap: spacing.xs },
  fieldLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 2,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerHighest,
    paddingVertical: spacing.sm,
    paddingHorizontal: 0,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: colors.onSurface,
    paddingVertical: spacing.sm,
  },
  pinInput: { letterSpacing: 8 },
  inputIcon: { fontSize: 18, color: colors.outlineVariant },
  iconBadge: {},
  inputUnderline: {
    height: 2,
    backgroundColor: colors.outlineVariant,
    opacity: 0.3,
    borderRadius: 1,
  },
  loginBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingVertical: spacing.md + 2,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  loginBtnDisabled: { opacity: 0.5 },
  loginBtnText: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: 15,
    letterSpacing: 1,
  },
  loginBtnArrow: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: 18,
  },
  footer: { alignItems: 'center', gap: spacing.md },
  footerLink: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: 13,
    borderBottomWidth: 1.5,
    borderBottomColor: colors.primaryFixedDim,
  },
  footerVersion: {
    fontSize: 9,
    color: colors.onSurfaceVariant,
    fontWeight: '500',
    letterSpacing: 3,
    textTransform: 'uppercase',
  },
});
