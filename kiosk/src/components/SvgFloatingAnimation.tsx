import React, { useEffect, useMemo } from 'react';
import { StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { vscale, scale, Spacing } from '../constants/theme';

interface SvgFloatingAnimationProps {
  index: number;
  SVGComponent: React.ReactNode;
  durationMs?: number;
}

/**
 * Component that animates SVG icons floating upward until they leave the screen.
 * Each icon starts at a random horizontal position and floats upward continuously.
 */
export default function SvgFloatingAnimation({
  index,
  SVGComponent,
  durationMs = 8000,
}: SvgFloatingAnimationProps) {
  const translateY = useSharedValue(vscale(600)); // Start at bottom
  const opacity = useSharedValue(1);

  useEffect(() => {
    // Start animation at different times for staggered effect
    const delay = index * 500;
    
    const timer = setTimeout(() => {
      // Animate upward from bottom to top (off-screen)
      translateY.value = withRepeat(
        withTiming(-vscale(700), {
          duration: durationMs,
          easing: Easing.linear,
        }),
        -1,
        false
      );

      // Fade out as it leaves
      opacity.value = withRepeat(
        withTiming(0, {
          duration: durationMs * 0.9,
          easing: Easing.in(Easing.ease),
        }),
        -1,
        false
      );
    }, delay);

    return () => clearTimeout(timer);
  }, [index, durationMs, translateY, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: translateY.value }],
    opacity: opacity.value,
  }));

  // Memoize random position so it stays stable across re-renders
  const randomLeft = useMemo(() => Math.random() * 100, []);

  return (
    <Animated.View
      style={[
        styles.container,
        { left: `${randomLeft}%` as any },
        animatedStyle,
      ]}
    >
      {SVGComponent}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    width: scale(60),
    height: scale(60),
    justifyContent: 'center',
    alignItems: 'center',
  },
});
