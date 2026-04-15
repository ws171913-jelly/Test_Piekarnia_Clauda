import React, { useCallback, useEffect, useState } from 'react';
import {
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, spacing } from './theme';

function MatIcon({ name, filled, size = 24, color }: { name: string; filled?: boolean; size?: number; color?: string }) {
  if (Platform.OS === 'web') {
    return (
      <span
        className="material-symbols-outlined"
        style={{
          fontSize: size,
          color: color ?? 'inherit',
          fontVariationSettings: filled ? "'FILL' 1, 'wght' 400" : "'FILL' 0, 'wght' 400",
          lineHeight: 1,
          display: 'block',
        }}
      >
        {name}
      </span>
    );
  }
  // Native fallback — keep emoji for now
  const map: Record<string, string> = { dashboard: '🏠', history: '🕐', person: '👤' };
  return <Text style={{ fontSize: size, color }}>{map[name] ?? name}</Text>;
}
import { userStore } from './store/userStore';

import LoginScreen from './screens/LoginScreen';
import ChangePinScreen from './screens/ChangePinScreen';
import BalanceScreen from './screens/BalanceScreen';
import CodeDisplayScreen from './screens/CodeDisplayScreen';
import HistoryScreen from './screens/HistoryScreen';
import ProfileScreen from './screens/ProfileScreen';

type Screen =
  | 'login'
  | 'changePin'
  | 'dashboard'
  | 'code'
  | 'history'
  | 'profileChangePin';

type Tab = 'dashboard' | 'profile';

export default function App() {
  const [screen, setScreen] = useState<Screen>('login');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [changePinReturnTo, setChangePinReturnTo] = useState<Screen>('dashboard');

  // Restore session on mount
  useEffect(() => {
    const session = userStore.getSession();
    if (session) {
      if (session.mustChangePin) {
        setScreen('changePin');
      } else {
        setScreen('dashboard');
      }
    }
  }, []);

  const handleLoginSuccess = useCallback((mustChangePin: boolean) => {
    if (mustChangePin) {
      setChangePinReturnTo('dashboard');
      setScreen('changePin');
    } else {
      setScreen('dashboard');
    }
  }, []);

  const handlePinChanged = useCallback(() => {
    setScreen(changePinReturnTo);
    setActiveTab('dashboard');
  }, [changePinReturnTo]);

  const handleLogout = useCallback(() => {
    setScreen('login');
    setActiveTab('dashboard');
  }, []);

  const handleProfileChangePin = useCallback(() => {
    setChangePinReturnTo('dashboard');
    setScreen('profileChangePin');
  }, []);

  if (screen === 'login') {
    return (
      <SafeAreaView style={styles.flex}>
        <LoginScreen onLoginSuccess={handleLoginSuccess} />
      </SafeAreaView>
    );
  }

  if (screen === 'changePin' || screen === 'profileChangePin') {
    return (
      <SafeAreaView style={styles.flex}>
        <ChangePinScreen onPinChanged={handlePinChanged} />
      </SafeAreaView>
    );
  }

  if (screen === 'code') {
    return (
      <SafeAreaView style={styles.flex}>
        <CodeDisplayScreen onBack={() => setScreen('dashboard')} />
      </SafeAreaView>
    );
  }

  if (screen === 'history') {
    return (
      <SafeAreaView style={styles.flex}>
        <HistoryScreen onBack={() => setScreen('dashboard')} />
      </SafeAreaView>
    );
  }

  // Main app with bottom tabs (dashboard / profile)
  return (
    <SafeAreaView style={styles.flex}>
      <View style={styles.flex}>
        {activeTab === 'dashboard' ? (
          <BalanceScreen
            onGenerateCode={() => setScreen('code')}
            onViewHistory={() => setScreen('history')}
            onLogout={handleLogout}
          />
        ) : (
          <ProfileScreen
            onChangePin={handleProfileChangePin}
            onLogout={handleLogout}
          />
        )}

        {/* Bottom Tab Bar */}
        <View style={styles.tabBar}>
          <Pressable
            style={[styles.tabItem, activeTab === 'dashboard' && styles.tabItemActive]}
            onPress={() => setActiveTab('dashboard')}
          >
            <MatIcon
              name="dashboard"
              filled={activeTab === 'dashboard'}
              size={24}
              color={activeTab === 'dashboard' ? colors.onPrimary : colors.onSurfaceVariant}
            />
            <Text style={[styles.tabLabel, activeTab === 'dashboard' && styles.tabLabelActive]}>
              Dashboard
            </Text>
          </Pressable>

          <Pressable
            style={styles.tabItem}
            onPress={() => setScreen('history')}
          >
            <MatIcon name="history" size={24} color={colors.onSurfaceVariant} />
            <Text style={styles.tabLabel}>Historia</Text>
          </Pressable>

          <Pressable
            style={[styles.tabItem, activeTab === 'profile' && styles.tabItemActive]}
            onPress={() => setActiveTab('profile')}
          >
            <MatIcon
              name="person"
              filled={activeTab === 'profile'}
              size={24}
              color={activeTab === 'profile' ? colors.onPrimary : colors.onSurfaceVariant}
            />
            <Text style={[styles.tabLabel, activeTab === 'profile' && styles.tabLabelActive]}>
              Profil
            </Text>
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface + 'cc',
    borderTopWidth: 1,
    borderTopColor: colors.outlineVariant + '26',
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    paddingBottom: spacing.lg,
    paddingTop: spacing.sm,
    paddingHorizontal: spacing.md,
    shadowColor: '#221a0e',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.04,
    shadowRadius: 20,
    elevation: 8,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: 999,
    gap: 2,
  },
  tabItemActive: {
    backgroundColor: colors.primary,
  },
  tabLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: colors.onSurfaceVariant,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginTop: 2,
  },
  tabLabelActive: { color: colors.onPrimary },
});
