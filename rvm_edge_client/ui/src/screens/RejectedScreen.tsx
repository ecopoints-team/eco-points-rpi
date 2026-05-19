import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function RejectedScreen() {
  const { payload, dispatch } = useKiosk();

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <StatusBadge label="Bottles Rejected" variant="error" />
      <Text style={styles.title}>Bottles Not Accepted</Text>
      <Text style={styles.reason}>
        {payload.reason ?? 'Unable to verify the bottles.'}
      </Text>
      <View style={styles.buttonRow}>
        <GlowButton
          label="Try Again"
          onPress={() => {
            dispatch({ type: 'REPEAT_READY' });
            if (!DEV_MODE) {
              sendGPIOEvent({ action: 'REPEAT_READY' });
            }
          }}
          style={styles.btn}
        />
        <GlowButton
          label="End Transaction"
          variant="outline"
          onPress={() => {
            dispatch({ type: 'ADVANCE_THANK_YOU' });
            if (!DEV_MODE) {
              sendGPIOEvent({ action: 'FINISH' });
            }
          }}
          style={styles.btn}
        />
      </View>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.error,
    textAlign: 'center',
  },
  reason: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.body,
    textAlign: 'center',
    maxWidth: 500,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: Spacing.md,
  },
  btn: { minWidth: 140 },
});
