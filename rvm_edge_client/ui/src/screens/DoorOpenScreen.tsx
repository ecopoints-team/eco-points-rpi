import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import StatusBadge from '../components/StatusBadge';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function DoorOpenScreen() {
  const { dispatch } = useKiosk();

  return (
    <LinearGradient
      colors={['#FEE2E2', '#FECACA', '#FEE2E2']}
      style={styles.container}
    >
      <LogoHeader />
      <StatusBadge label="DOOR OPEN" variant="error" />
      <Text style={styles.title}>Please close the door to proceed.</Text>
      <Text style={styles.subtitle}>
        The machine will process your bottles once the door is closed.
      </Text>

      <GlowButton
        label="Cancel Session"
        variant="outline"
        onPress={() => {
          dispatch({ type: 'SYSTEM_CLEAR' });
          if (!DEV_MODE) {
            sendGPIOEvent({ action: 'CANCEL' });
          }
        }}
        style={styles.cancelBtn}
      />
    </LinearGradient>
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
    maxWidth: 500,
  },
  cancelBtn: {
    marginTop: Spacing.lg,
    minWidth: 180,
  },
});
