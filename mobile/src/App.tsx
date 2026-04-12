import React, { useCallback, useEffect, useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { colors, spacing } from './theme';
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
            <Text style={[styles.tabIcon, activeTab === 'dashboard' && styles.tabIconActive]}>
              🏠
            </Text>
            <Text style={[styles.tabLabel, activeTab === 'dashboard' && styles.tabLabelActive]}>
              Dashboard
            </Text>
          </Pressable>

          <Pressable
            style={[styles.tabItem, false && styles.tabItemActive]}
            onPress={() => setScreen('history')}
          >
            <Text style={styles.tabIcon}>🕐</Text>
            <Text style={styles.tabLabel}>Historia</Text>
          </Pressable>

          <Pressable
            style={[styles.tabItem, activeTab === 'profile' && styles.tabItemActive]}
            onPress={() => setActiveTab('profile')}
          >
            <Text style={[styles.tabIcon, activeTab === 'profile' && styles.tabIconActive]}>
              👤
            </Text>
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
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.outlineVariant,
    paddingBottom: spacing.md,
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
    borderRadius: 12,
    gap: 2,
  },
  tabItemActive: {
    backgroundColor: colors.primary,
  },
  tabIcon: { fontSize: 20 },
  tabIconActive: {},
  tabLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.onSurfaceVariant,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  tabLabelActive: { color: colors.onPrimary },
});
