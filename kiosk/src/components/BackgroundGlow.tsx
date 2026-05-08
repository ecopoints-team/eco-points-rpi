import React, { useEffect } from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import HexGridPattern from './HexGridPattern';
import PulsingRings from './PulsingRings';
import FloatingEcoIcons from './FloatingEcoIcons';
import { Colors } from '../constants/theme';

interface Props {
  style?: ViewStyle;
  children?: React.ReactNode;
  dark?: boolean;
}

export default function BackgroundGlow({ style, children, dark = false }: Props) {
  const colors = dark
    ? ([Colors.heading, Colors.hover, '#043927'] as const)
    : ([Colors.bgTint, Colors.bg, '#ECFDF5'] as const);

  // Animated opacity for blobs to create breathing glow effect
  const blobOpacity1 = useSharedValue(0.07);
  const blobOpacity2 = useSharedValue(0.07);
  const blobOpacity3 = useSharedValue(0.05);

  // Glow ring scale for orb pulsing
  const glowScale1 = useSharedValue(1);
  const glowScale2 = useSharedValue(1);

  useEffect(() => {
    // Stagger blob animations
    blobOpacity1.value = withRepeat(
      withSequence(
        withTiming(0.15, { duration: 3200, easing: Easing.inOut(Easing.ease) }),
        withTiming(0.07, { duration: 3200, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );

    blobOpacity2.value = withRepeat(
      withSequence(
        withTiming(0.12, { duration: 4000, easing: Easing.inOut(Easing.ease) }),
        withTiming(0.05, { duration: 4000, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );

    blobOpacity3.value = withRepeat(
      withSequence(
        withTiming(0.1, { duration: 3600, easing: Easing.inOut(Easing.ease) }),
        withTiming(0.04, { duration: 3600, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );

    // Glow ring pulse
    glowScale1.value = withRepeat(
      withSequence(
        withTiming(1.3, { duration: 2800, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 2800, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );

    glowScale2.value = withRepeat(
      withSequence(
        withTiming(1.25, { duration: 3400, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 3400, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );
  }, []);

  const animStyle1 = useAnimatedStyle(() => ({
    opacity: blobOpacity1.value,
  }));

  const animStyle2 = useAnimatedStyle(() => ({
    opacity: blobOpacity2.value,
  }));

  const animStyle3 = useAnimatedStyle(() => ({
    opacity: blobOpacity3.value,
  }));

  const glowRingStyle1 = useAnimatedStyle(() => ({
    transform: [{ scale: glowScale1.value }],
    opacity: blobOpacity1.value * 0.5,
  }));

  const glowRingStyle2 = useAnimatedStyle(() => ({
    transform: [{ scale: glowScale2.value }],
    opacity: blobOpacity2.value * 0.5,
  }));

  return (
    <LinearGradient colors={colors} style={[styles.container, style]}>
      {/* Hex grid pattern (tech feel) */}
      <HexGridPattern variant={dark ? 'dark' : 'light'} />

      {/* Pulsing rings animation */}
      <PulsingRings />

      {/* Floating eco icons */}
      <FloatingEcoIcons count={5} />

      {/* Decorative blobs with glow rings */}
      <Animated.View style={[styles.blob, styles.blobTL, dark && styles.blobDark, animStyle1]} />
      <Animated.View style={[styles.glowRing, styles.glowRingTL, glowRingStyle1]} />

      <Animated.View style={[styles.blob, styles.blobBR, dark && styles.blobDark, animStyle2]} />
      <Animated.View style={[styles.glowRing, styles.glowRingBR, glowRingStyle2]} />

      <Animated.View style={[styles.blob, styles.blobCenter, dark && styles.blobDark, animStyle3]} />

      {children}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
    overflow: 'hidden',
  },
  // Orb blobs
  blob: {
    position: 'absolute',
    width: 400,
    height: 400,
    borderRadius: 200,
    backgroundColor: Colors.primary,
    opacity: 0.07,
  },
  blobDark: {
    backgroundColor: Colors.primaryLight,
    opacity: 0.12,
  },
  blobTL: {
    top: -120,
    left: -80,
  },
  blobBR: {
    bottom: -100,
    right: -60,
  },
  blobCenter: {
    top: '50%',
    right: '10%',
    width: 300,
    height: 300,
    borderRadius: 150,
  },
  // Glow rings around orbs
  glowRing: {
    position: 'absolute',
    borderRadius: 250,
    borderWidth: 1.5,
    borderColor: Colors.primaryLight,
    width: 500,
    height: 500,
  },
  glowRingTL: {
    top: -170,
    left: -130,
  },
  glowRingBR: {
    bottom: -150,
    right: -110,
  },
});
