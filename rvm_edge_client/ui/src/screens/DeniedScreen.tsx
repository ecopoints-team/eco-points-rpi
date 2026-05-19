import React from 'react';
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function DeniedScreen() {
  const { dispatch } = useKiosk();

  return (
    <TouchableOpacity
      style={{ flex: 1 }}
      activeOpacity={1}
      onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
    >
      <BackgroundGlow style={styles.container}>
        <LogoHeader />
        <StatusBadge label="ACCESS DENIED" variant="warning" />
        <Text style={styles.title}>Account Not Recognized</Text>
        <Text style={styles.body}>
          Please check your QR code and try again.{'\n'}
          If the problem persists, contact support.
        </Text>
        <Text style={styles.hint}>Tap anywhere to return to start</Text>
      </BackgroundGlow>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.heading,
    textAlign: 'center',
  },
  body: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.body,
    textAlign: 'center',
    lineHeight: FontSizes.lg * 1.6,
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.body,
    marginTop: Spacing.sm,
  },
});
