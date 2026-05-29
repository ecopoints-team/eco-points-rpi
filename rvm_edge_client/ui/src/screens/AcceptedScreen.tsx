import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import GlowButton from '../components/GlowButton';
import { LinearGradient } from 'expo-linear-gradient';
import PointsDisplay from '../components/PointsDisplay';
import StatusBadge from '../components/StatusBadge';
import LogoHeader from '../components/LogoHeader';
import PulsingRings from '../components/PulsingRings';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function AcceptedScreen() {
  const { payload, dispatch } = useKiosk();

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={[Colors.bgTint, '#DCFCE7', Colors.bgTint]}
        style={styles.innerContainer}
      >
        <PulsingRings />
        <LogoHeader />
        <StatusBadge label="Bottles Accepted" variant="success" />
        <PointsDisplay value={payload.points ?? 0} />
        <Text style={styles.bottles}>
          {payload.bottleCount ?? 0} bottle{(payload.bottleCount ?? 0) !== 1 ? 's' : ''} recycled
        </Text>
        <View style={styles.buttonRow}>
          <GlowButton
            label="Transact again"
            onPress={() => {
              dispatch({ type: 'REPEAT_READY' });
              if (!DEV_MODE) {
                sendGPIOEvent({ action: 'REPEAT_READY' });
              }
            }}
            style={styles.btn}
          />
          <GlowButton
            label="Finish"
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
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  innerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
    overflow: 'hidden',
  },
  bottles: {
    fontFamily: Fonts.mono,
    fontSize: FontSizes.lg,
    color: Colors.primaryDark,
    letterSpacing: 1,
  },
  buttonRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.md },
  btn: { minWidth: 120 },
});
