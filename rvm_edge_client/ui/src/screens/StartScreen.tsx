import React, { useEffect } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import PulsingRings from '../components/PulsingRings';
import HexGridPattern from '../components/HexGridPattern';
import FloatingEcoIcons from '../components/FloatingEcoIcons';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing, scale } from '../constants/theme';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';

export default function StartScreen() {
  const { payload, dispatch } = useKiosk();
  const pulse = useSharedValue(1);

  useEffect(() => {
    pulse.value = withRepeat(
      withSequence(
        withTiming(1.18, { duration: 1200 }),
        withTiming(1, { duration: 1200 })
      ),
      -1,
      true
    );
  }, []);

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
    opacity: 0.15 + (pulse.value - 1) * 0.4,
  }));

  return (
    <LinearGradient
      colors={[Colors.bg, Colors.bgTint, '#ECFDF5']}
      style={styles.container}
    >
      {/* Background layers */}
      <HexGridPattern />
      <PulsingRings />
      <FloatingEcoIcons count={4} />

      {/* Pulsing ring - logo background */}
      <Animated.View style={[styles.ring, pulseStyle]} />

      {/* Logo area */}
      <View style={styles.content}>
        <Image
          source={require('../../assets/favicon.png')}
          style={styles.logo}
          resizeMode="contain"
        />
        <Text style={styles.title}>Welcome to EcoPoints</Text>
        <Text style={styles.subtitle}>Smart Recycling Kiosk</Text>

        {/* Visible Start Button */}
        <GlowButton
          label="Start"
          onPress={() => {
            dispatch({ type: 'WAKE' });
            if (!DEV_MODE) {
              sendGPIOEvent({ action: 'WAKE' });
            }
          }}
          style={styles.startBtn}
        />
      </View>

      {/* Bin Full Notification Badge */}
      {payload.isBinFull && (
        <View style={styles.binFullBadge}>
          <Text style={styles.binFullIcon}>⚠</Text>
          <View>
            <Text style={styles.binFullTitle}>Bin Full</Text>
            <Text style={styles.binFullText}>Staff has been notified</Text>
          </View>
        </View>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  ring: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    borderWidth: 3,
    borderColor: Colors.primary,
  },
  content: {
    alignItems: 'center',
    zIndex: 10,
  },
  logo: {
    width: scale(150),
    height: scale(150),
    marginTop: Spacing.lg,
    marginBottom: Spacing.sm,
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.hero,
    color: Colors.heading,
    letterSpacing: 2,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.primaryDark,
    marginTop: Spacing.xs,
    letterSpacing: 1,
  },
  startBtn: {
    marginTop: Spacing.lg,
    minWidth: scale(240),
    paddingVertical: Spacing.sm,
  },
  // Bin full notification badge
  binFullBadge: {
    position: 'absolute',
    bottom: Spacing.md,
    right: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    backgroundColor: 'rgba(146, 64, 14, 0.12)',
    borderWidth: 1,
    borderColor: '#F59E0B',
    borderRadius: 12,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    zIndex: 20,
  },
  binFullIcon: {
    fontSize: FontSizes.lg,
  },
  binFullTitle: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.sm,
    color: '#92400E',
  },
  binFullText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.xs,
    color: '#78350F',
    opacity: 0.8,
  },
});
