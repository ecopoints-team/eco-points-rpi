import React from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useAnimatedStyle,
} from 'react-native-reanimated';
import { useGlobalPulseAnimation } from '../hooks/useGlobalPulseAnimation';
import { Colors, scale, vscale } from '../constants/theme';

interface PulseRingProps {
  size: number;
  duration: number;
  delay: number;
  top?: number;
  bottom?: number;
  left?: number;
  right?: number;
}

function PulseRing({ size, duration, delay, top, bottom, left, right }: PulseRingProps) {
  const { scale: scale_val, opacity } = useGlobalPulseAnimation(duration, delay);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale_val.value }],
    opacity: opacity.value,
  }));

  return (
    <Animated.View
      style={[
        styles.ring,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          top,
          bottom,
          left,
          right,
        },
        animStyle,
      ]}
    />
  );
}

export default function PulsingRings() {
  return (
    <View style={styles.container} pointerEvents="none">
      {/* Top right ring - larger, 3s duration */}
      <PulseRing size={96} duration={3000} delay={0} top={vscale(120)} right={scale(150)} />

      {/* Bottom left ring - smaller, 4s duration, 1s delay */}
      <PulseRing size={64} duration={4000} delay={1000} bottom={vscale(180)} left={scale(100)} />
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
  },
  ring: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: Colors.primary,
    opacity: 0.15,
  },
});
