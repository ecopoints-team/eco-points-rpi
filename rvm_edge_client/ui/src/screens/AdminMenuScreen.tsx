import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing, scale } from '../constants/theme';

export default function AdminMenuScreen() {
  const { payload, dispatch } = useKiosk();

  const categories = [
    { key: 'maintenance' as const, label: 'Maintenance', icon: 'tool' as const, desc: 'Cable, Sensor, Camera, Motor' },
    { key: 'diagnostics' as const, label: 'Diagnostics', icon: 'activity' as const, desc: 'Machine Checkup, Software Update' },
    { key: 'clearing' as const, label: 'Clearing', icon: 'trash-2' as const, desc: 'Bin Full, Storage Reset' },
  ];

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <StatusBadge label="ADMIN MODE" variant="warning" />

      <Text style={styles.welcome}>
        Welcome, {payload.userName ?? 'Admin'}
      </Text>
      <Text style={styles.subtitle}>Select a concern to address</Text>

      <View style={styles.grid}>
        {categories.map((cat) => (
          <GlowButton
            key={cat.key}
            label={cat.label}
            onPress={() =>
              dispatch({ type: 'ADMIN_SELECT_CATEGORY', payload: { category: cat.key } })
            }
            style={styles.categoryBtn}
          />
        ))}
      </View>

      <GlowButton
        label="Exit Admin"
        variant="outline"
        onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
        style={styles.exitBtn}
      />
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
  },
  welcome: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    textAlign: 'center',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: Spacing.sm,
    marginTop: Spacing.xs,
  },
  categoryBtn: {
    minWidth: scale(130),
    paddingVertical: Spacing.xs,
  },
  exitBtn: {
    minWidth: 160,
    marginTop: Spacing.sm,
  },
});
