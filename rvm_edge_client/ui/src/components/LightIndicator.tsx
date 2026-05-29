import React, { useEffect, useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { useKiosk, KioskState } from '../context/KioskContext';
import { scale } from '../constants/theme';

function getLightColor(screen: KioskState, isBinFull?: boolean): 'red' | 'green' | 'yellow' | 'off' {
  if (screen === 'ADMIN_MENU' || screen === 'ADMIN_ACTION' || screen === 'ADMIN_NOTES') return 'red';
  if (screen === 'BIN_FULL_DENIED') return 'red';
  switch (screen) {
    case 'START':
    case 'IDLE':
      return isBinFull ? 'red' : 'off';
    case 'QR_SCAN':
      return 'off';
    case 'READY':
    case 'ACCEPTED':
      return 'green';
    case 'VERIFYING':
    case 'DOOR_OPEN':
      return 'yellow';
    case 'REJECTED':
    case 'DENIED':
      return 'red';
    case 'THANK_YOU':
      return 'green';
    default:
      return 'off';
  }
}

const COLOR_MAP = {
  red: '#EF4444',
  green: '#10B981',
  yellow: '#FBBF24',
  off: '#9CA3AF',
};

const GLOW_MAP = {
  red: 'rgba(239, 68, 68, 0.4)',
  green: 'rgba(16, 185, 129, 0.4)',
  yellow: 'rgba(251, 191, 36, 0.4)',
  off: 'rgba(156, 163, 175, 0.15)',
};

export default function LightIndicator() {
  const { screen, payload } = useKiosk();
  const color = getLightColor(screen, payload.isBinFull);
  const pulse = useSharedValue(1);
  const isActive = color !== 'off';

  useEffect(() => {
    if (!isActive) {
      pulse.value = withTiming(1, { duration: 300 });
      return;
    }
    pulse.value = withRepeat(
      withSequence(
        withTiming(1.5, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );
  }, [isActive]);

  const glowStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
  }));

  // Derive static styles from the current color (not in worklet)
  const dotColor = COLOR_MAP[color];
  const glowColor = GLOW_MAP[color];
  const glowOpacity = isActive ? 0.6 : 0.3;

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.glow,
          { backgroundColor: glowColor, opacity: glowOpacity },
          glowStyle,
        ]}
      />
      <View style={[styles.dot, { backgroundColor: dotColor }]} />
    </View>
  );
}

const DOT_SIZE = scale(14);
const GLOW_SIZE = scale(32);

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: scale(18),
    right: scale(18),
    width: GLOW_SIZE,
    height: GLOW_SIZE,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9998,
  },
  glow: {
    position: 'absolute',
    width: GLOW_SIZE,
    height: GLOW_SIZE,
    borderRadius: GLOW_SIZE / 2,
  },
  dot: {
    width: DOT_SIZE,
    height: DOT_SIZE,
    borderRadius: DOT_SIZE / 2,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.8)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
});
