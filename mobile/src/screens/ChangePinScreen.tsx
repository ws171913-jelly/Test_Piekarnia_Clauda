import React, { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { colors, radius, spacing } from '../theme';
import { changePin } from '../services/api';
import { userStore } from '../store/userStore';

interface Props {
  onPinChanged: () => void;
}

export default function ChangePinScreen({ onPinChanged }: Props) {
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleChangePin() {
    if (newPin.length < 4) {
      setError('PIN musi mieć co najmniej 4 cyfry');
      return;
    }
    if (newPin !== confirmPin) {
      setError('PIN-y nie pasują do siebie');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await changePin(newPin, confirmPin);
      const session = userStore.getSession();
      if (session) {
        userStore.saveSession({
          ...session,
          accessToken: result.access_token,
          mustChangePin: false,
        });
      }
      onPinChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd zmiany PIN');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.iconCircle}>
            <Text style={styles.iconText}>🔑</Text>
          </View>
          <Text style={styles.title}>Wymagana zmiana PIN-u</Text>
          <Text style={styles.subtitle}>
            Dla Twojego bezpieczeństwa, prosimy o zaktualizowanie kodu dostępu.
          </Text>
        </View>

        {/* PIN dots indicator */}
        <View style={styles.dotsRow}>
          {[0, 1, 2, 3].map((i) => (
            <View
              key={i}
              style={[styles.dot, newPin.length > i && styles.dotFilled]}
            />
          ))}
        </View>

        {/* Form */}
        <View style={styles.formCard}>
          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* New PIN */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>NOWY PIN</Text>
            <View style={styles.inputCard}>
              <TextInput
                style={styles.input}
                value={newPin}
                onChangeText={setNewPin}
                secureTextEntry={!showNew}
                maxLength={6}
                keyboardType="number-pad"
                editable={!loading}
                placeholder="••••"
                placeholderTextColor={colors.outlineVariant}
              />
              <Pressable onPress={() => setShowNew((v) => !v)}>
                <Text style={styles.visibilityIcon}>{showNew ? '👁️' : '🙈'}</Text>
              </Pressable>
            </View>
          </View>

          {/* Confirm PIN */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>POWTÓRZ PIN</Text>
            <View style={styles.inputCard}>
              <TextInput
                style={styles.input}
                value={confirmPin}
                onChangeText={setConfirmPin}
                secureTextEntry={!showConfirm}
                maxLength={6}
                keyboardType="number-pad"
                editable={!loading}
                placeholder="••••"
                placeholderTextColor={colors.outlineVariant}
              />
              <Pressable onPress={() => setShowConfirm((v) => !v)}>
                <Text style={styles.visibilityIcon}>{showConfirm ? '👁️' : '🙈'}</Text>
              </Pressable>
            </View>
          </View>

          {/* Hint */}
          <View style={styles.hintBox}>
            <Text style={styles.hintText}>
              💡 Nowy PIN powinien składać się z 4–6 cyfr. Unikaj prostych kombinacji takich jak
              „1234" lub daty urodzin.
            </Text>
          </View>

          {/* Submit */}
          <Pressable
            style={[styles.submitBtn, loading && styles.submitBtnDisabled]}
            onPress={handleChangePin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : (
              <Text style={styles.submitBtnText}>Ustaw PIN</Text>
            )}
          </Pressable>

          <Text style={styles.helpText}>
            Problem z logowaniem?{' '}
            <Text style={styles.helpLink}>Skontaktuj się z obsługą</Text>
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  container: {
    flexGrow: 1,
    padding: spacing.lg,
    gap: spacing.xl,
    backgroundColor: colors.surface,
  },
  header: { alignItems: 'center', gap: spacing.sm, paddingTop: spacing.lg },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surfaceContainerHigh,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: { fontSize: 32 },
  title: {
    fontFamily: 'serif',
    fontSize: 26,
    fontWeight: '700',
    fontStyle: 'italic',
    color: colors.primary,
    textAlign: 'center',
    lineHeight: 32,
  },
  subtitle: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    lineHeight: 20,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colors.outlineVariant,
    backgroundColor: 'transparent',
  },
  dotFilled: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  formCard: {
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: radius.xl,
    padding: spacing.xl,
    gap: spacing.lg,
  },
  errorBanner: {
    backgroundColor: colors.errorContainer,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  errorText: { color: colors.onErrorContainer, fontSize: 13, fontWeight: '600' },
  fieldGroup: { gap: spacing.xs },
  fieldLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 2,
  },
  inputCard: {
    backgroundColor: colors.surfaceContainerHighest,
    borderRadius: radius.xl,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    fontSize: 20,
    color: colors.onSurface,
    letterSpacing: 8,
  },
  visibilityIcon: { fontSize: 20 },
  hintBox: {
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  hintText: {
    fontSize: 11,
    color: colors.onSurfaceVariant,
    lineHeight: 18,
  },
  submitBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    paddingVertical: spacing.md + 2,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: 15,
    letterSpacing: 1,
  },
  helpText: { textAlign: 'center', fontSize: 11, color: colors.outline },
  helpLink: { color: colors.primary, textDecorationLine: 'underline' },
});
