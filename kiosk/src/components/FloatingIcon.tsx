import React, { useEffect, useMemo } from 'react';
import { StyleSheet, Text } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  withDelay,
} from 'react-native-reanimated';

interface Props {
  icon?: string;
  index?: number;
}

const ICONS = ['🍃', '♻️', '🌿', '💚', '🌱', '🍀'];

export default function FloatingIcon({ icon, index = 0 }: Props) {
  const symbol = icon ?? ICONS[index % ICONS.length];

  // Memoize random values so they stay stable across re-renders
  const { startX, duration, delayMs } = useMemo(() => ({
    startX: Math.random() * 900,
    duration: 6000 + Math.random() * 4000,
    delayMs: Math.random() * 3000,
  }), []);

  const translateY = useSharedValue(500);
  const translateX = useSharedValue(startX);
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withDelay(
      delayMs,
      withRepeat(
        withSequence(
          withTiming(0.8, { duration: 500 }),
          withTiming(0.8, { duration: duration - 1000 }),
          withTiming(0, { duration: 500 })
        ),
        -1,
        false
      )
    );

    translateY.value = withDelay(
      delayMs,
      withRepeat(
        withTiming(-80, { duration }),
        -1,
        false
      )
    );

    translateX.value = withDelay(
      delayMs,
      withRepeat(
        withSequence(
          withTiming(startX + 30, { duration: duration / 2 }),
          withTiming(startX - 30, { duration: duration / 2 })
        ),
        -1,
        true
      )
    );
  }, []);

  const animStyle = useAnimatedStyle(() => ({
    transform: [
      { translateY: translateY.value },
      { translateX: translateX.value },
    ],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[styles.icon, animStyle]}>
      <Text style={styles.text}>{symbol}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  icon: {
    position: 'absolute',
    bottom: 0,
  },
  text: {
    fontSize: 32,
  },
});
