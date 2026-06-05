import React from 'react';
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import RecyclingIcon from '../components/RecyclingIcon';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';

export default function IdleScreen() {
  const { dispatch } = useKiosk();

  return (
    <TouchableOpacity
      style={styles.touchable}
      activeOpacity={1}
      onPress={() => {
        dispatch({ type: 'WAKE' });
        if (!DEV_MODE) {
          sendGPIOEvent({ action: 'WAKE' });
        }
      }}
    >
      <BackgroundGlow style={styles.container}>
        <LogoHeader />
        <Text style={styles.title}>Insert Bottles to Begin</Text>
        <RecyclingIcon size={150} color={Colors.primary} animated={true} />
        <Text style={styles.tapHint}>Tap anywhere to start</Text>
      </BackgroundGlow>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  touchable: { flex: 1 },
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.lg,
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.heading,
    textAlign: 'center',
    lineHeight: FontSizes.xxl * 1.4,
  },
  tapHint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.primary,
    opacity: 0.6,
    position: 'absolute',
    bottom: Spacing.lg,
  },
});
