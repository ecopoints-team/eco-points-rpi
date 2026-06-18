import React, { useEffect, useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  withDelay,
  Easing,
} from 'react-native-reanimated';
import Svg, { Path, Circle, G } from 'react-native-svg';
import { Colors, scale, vscale } from '../constants/theme';

// SVG icon definitions (viewBox 0 0 24 24)
const ECO_ICONS = [
  // Leaf
  { path: 'M 12 2 C 17 4 20 10 18 16 C 16 20 12 22 8 20 C 4 18 2 14 4 8 C 6 4 10 2 12 2 Z', type: 'fill' as const },
  // Water drop
  { path: 'M 12 2 C 12 2 6 10 6 15 C 6 18.5 8.7 21.5 12 21.5 C 15.3 21.5 18 18.5 18 15 C 18 10 12 2 12 2 Z', type: 'stroke' as const },
  // Recycle arrows (simplified)
  { path: 'M 12 4 L 8 10 L 16 10 Z M 4 14 L 8 20 L 12 14 Z M 20 14 L 16 20 L 12 14 Z', type: 'fill' as const },
  // Small bottle outline
  { path: 'M 10 2 L 14 2 L 14 5 L 16 7 L 16 20 C 16 21 15 22 14 22 L 10 22 C 9 22 8 21 8 20 L 8 7 L 10 5 Z', type: 'stroke' as const },
];

interface IconConfig {
  icon: typeof ECO_ICONS[0];
  size: number;
  startX: number;
  duration: number;
  delay: number;
  opacity: number;
  color: string;
}

function generateIconConfigs(count: number): IconConfig[] {
  const configs: IconConfig[] = [];
  const colors = [Colors.primary, Colors.primaryLight, '#6EE7B7', Colors.primaryDark];

  for (let i = 0; i < count; i++) {
    const seed = (i * 41 + 17) % 100;
    configs.push({
      icon: ECO_ICONS[i % ECO_ICONS.length],
      size: scale(30 + (seed % 24)),
      startX: (i * 200 + 100) % 1100,
      duration: 12000 + (seed % 8) * 1000,
      delay: i * 1800,
      opacity: 0.05 + (seed % 8) * 0.008,
      color: colors[i % colors.length],
    });
  }
  return configs;
}

function FloatingEcoIcon({ config }: { config: IconConfig }) {
  const translateY = useSharedValue(vscale(680));
  const translateX = useSharedValue(0);
  const opacity = useSharedValue(0);

  useEffect(() => {
    translateY.value = withDelay(
      config.delay,
      withRepeat(
        withTiming(-vscale(80), {
          duration: config.duration,
          easing: Easing.linear,
        }),
        -1,
        false
      )
    );

    translateX.value = withDelay(
      config.delay,
      withRepeat(
        withSequence(
          withTiming(15, { duration: config.duration / 3, easing: Easing.inOut(Easing.ease) }),
          withTiming(-15, { duration: config.duration / 3, easing: Easing.inOut(Easing.ease) }),
          withTiming(0, { duration: config.duration / 3, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        false
      )
    );

    opacity.value = withDelay(
      config.delay,
      withRepeat(
        withSequence(
          withTiming(config.opacity, { duration: config.duration * 0.15 }),
          withTiming(config.opacity, { duration: config.duration * 0.65 }),
          withTiming(0, { duration: config.duration * 0.2 })
        ),
        -1,
        false
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
    <Animated.View style={[styles.icon, { left: config.startX }, animStyle]}>
      <Svg width={config.size} height={config.size} viewBox="0 0 24 24">
        <Path
          d={config.icon.path}
          fill={config.icon.type === 'fill' ? config.color : 'none'}
          stroke={config.color}
          strokeWidth={config.icon.type === 'stroke' ? 1.2 : 0}
          opacity={0.9}
        />
      </Svg>
    </Animated.View>
  );
}

interface FloatingEcoIconsProps {
  count?: number;
}

export default function FloatingEcoIcons({ count = 5 }: FloatingEcoIconsProps) {
  const configs = useMemo(() => generateIconConfigs(count), [count]);

  return (
    <View style={styles.container} pointerEvents="none">
      {configs.map((config, i) => (
        <FloatingEcoIcon key={i} config={config} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1,
    overflow: 'hidden',
  },
  icon: {
    position: 'absolute',
    bottom: -30,
  },
});
