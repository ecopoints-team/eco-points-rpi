import React from 'react';
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import StatusBadge from '../components/StatusBadge';
import LogoHeader from '../components/LogoHeader';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function DoorOpenScreen() {
  const { dispatch } = useKiosk();

  return (
    <TouchableOpacity
      style={{ flex: 1 }}
      activeOpacity={1}
      onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
    >
      <LinearGradient
        colors={['#FEE2E2', '#FECACA', '#FEE2E2']}
        style={styles.container}
      >
        <LogoHeader />
        <StatusBadge label="DOOR OPEN" variant="error" />
        <Text style={styles.title}>Please Close the Door</Text>
        <Text style={styles.subtitle}>The machine will process your bottles</Text>
        <Text style={styles.tap}>Tap anywhere to return to start</Text>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
    overflow: 'hidden',
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: '#991B1B',
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: '#7F1D1D',
    textAlign: 'center',
  },
  tap: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: '#7F1D1D',
    marginTop: Spacing.sm,
    opacity: 0.6,
  },
});
