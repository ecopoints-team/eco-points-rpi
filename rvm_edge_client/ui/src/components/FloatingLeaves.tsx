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
import Svg, { Path } from 'react-native-svg';
import { Colors, scale, vscale } from '../constants/theme';

const AnimatedView = Animated.View;

// Leaf SVG path shapes (variety)
const LEAF_PATHS = [
  // Simple leaf
  'M 10 0 C 15 5 18 15 10 25 C 2 15 5 5 10 0 Z',
  // Wider leaf
  'M 10 0 C 18 3 22 12 10 28 C -2 12 2 3 10 0 Z',
  // Slim leaf
  'M 8 0 C 12 6 14 18 8 30 C 2 18 4 6 8 0 Z',
];

interface LeafConfig {
  path: string;
  size: number;
  startX: number;
  duration: number;
  delay: number;
  swayAmount: number;
  rotateStart: number;
  rotateEnd: number;
  opacity: number;
  color: string;
}

function generateLeafConfigs(count: number): LeafConfig[] {
  const configs: LeafConfig[] = [];
  const colors = [Colors.primary, Colors.primaryLight, Colors.primaryDark, '#6EE7B7'];
  
  for (let i = 0; i < count; i++) {
    const seed = (i * 37 + 11) % 100;
    configs.push({
      path: LEAF_PATHS[i % LEAF_PATHS.length],
      size: 16 + (seed % 20),
      startX: (i * 150 + 80) % 1000,
      duration: 10000 + (seed % 6) * 1000,
      delay: i * 1200,
      swayAmount: 20 + (seed % 30),
      rotateStart: -20 + (seed % 40),
      rotateEnd: 20 + (seed % 60),
      opacity: 0.06 + (seed % 10) * 0.01,
      color: colors[i % colors.length],
    });
  }
  return configs;
}

function FloatingLeaf({ config }: { config: LeafConfig }) {
  const translateY = useSharedValue(vscale(650));
  const translateX = useSharedValue(0);
  const rotate = useSharedValue(config.rotateStart);
  const opacity = useSharedValue(0);

  useEffect(() => {
    // Float upward
    translateY.value = withDelay(
      config.delay,
      withRepeat(
        withTiming(-vscale(100), {
          duration: config.duration,
          easing: Easing.linear,
        }),
        -1,
        false
      )
    );

    // Horizontal sway
    translateX.value = withDelay(
      config.delay,
      withRepeat(
        withSequence(
          withTiming(config.swayAmount, { duration: config.duration / 4, easing: Easing.inOut(Easing.ease) }),
          withTiming(-config.swayAmount, { duration: config.duration / 2, easing: Easing.inOut(Easing.ease) }),
          withTiming(0, { duration: config.duration / 4, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        false
      )
    );

    // Gentle rotation
    rotate.value = withDelay(
      config.delay,
      withRepeat(
        withSequence(
          withTiming(config.rotateEnd, { duration: config.duration / 2, easing: Easing.inOut(Easing.ease) }),
          withTiming(config.rotateStart, { duration: config.duration / 2, easing: Easing.inOut(Easing.ease) })
        ),
        -1,
        true
      )
    );

    // Fade in/out cycle
    opacity.value = withDelay(
      config.delay,
      withRepeat(
        withSequence(
          withTiming(config.opacity, { duration: config.duration * 0.1 }),
          withTiming(config.opacity, { duration: config.duration * 0.7 }),
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
      { rotate: `${rotate.value}deg` },
    ],
    opacity: opacity.value,
  }));

  return (
    <AnimatedView
      style={[
        styles.leaf,
        { left: config.startX },
        animStyle,
      ]}
    >
      <Svg width={config.size} height={config.size * 1.5} viewBox="0 0 20 30">
        <Path
          d={config.path}
          fill={config.color}
          opacity={0.8}
        />
        {/* Leaf vein */}
        <Path
          d="M 10 2 L 10 24"
          stroke={config.color}
          strokeWidth={0.5}
          opacity={0.4}
        />
      </Svg>
    </AnimatedView>
  );
}

interface FloatingLeavesProps {
  count?: number;
}

export default function FloatingLeaves({ count = 8 }: FloatingLeavesProps) {
  const configs = useMemo(() => generateLeafConfigs(count), [count]);

  return (
    <View style={styles.container} pointerEvents="none">
      {configs.map((config, i) => (
        <FloatingLeaf key={i} config={config} />
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
  leaf: {
    position: 'absolute',
    bottom: -40,
  },
});
