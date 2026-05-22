import React, { useEffect } from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
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
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing, scale, vscale } from '../constants/theme';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';

export default function StartScreen() {
  const { dispatch } = useKiosk();
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
    <TouchableOpacity
      style={{ flex: 1 }}
      activeOpacity={1}
      onPress={() => {
        dispatch({ type: 'WAKE' });
        if (!DEV_MODE) {
          sendGPIOEvent({ action: 'WAKE' });
        }
      }}
    >
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
          <Text style={styles.title}>EcoPoints</Text>
          <Text style={styles.subtitle}>Smart Recycling Kiosk</Text>
          <Text style={styles.tapHint}>Tap to start</Text>
        </View>
      </LinearGradient>
    </TouchableOpacity>
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
    width: scale(80),
    height: scale(80),
    marginBottom: Spacing.sm,
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.hero,
    color: Colors.heading,
    letterSpacing: 2,
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.primaryDark,
    marginTop: Spacing.xs,
    letterSpacing: 1,
  },
  tapHint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.primary,
    marginTop: Spacing.md,
    opacity: 0.7,
  },
});
