import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import Svg, { Path, Circle } from 'react-native-svg';
import { Colors } from '../constants/theme';

interface Props {
  size?: number;
  color?: string;
  animated?: boolean;
}

export default function PetBottleIcon({ size = 100, color = Colors.primary, animated = true }: Props) {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  useEffect(() => {
    if (animated) {
      scale.value = withRepeat(
        withSequence(
          withTiming(1.08, { duration: 1500 }),
          withTiming(1, { duration: 1500 })
        ),
        -1,
        true
      );
      opacity.value = withRepeat(
        withSequence(
          withTiming(0.6, { duration: 1500 }),
          withTiming(1, { duration: 1500 })
        ),
        -1,
        true
      );
    }
  }, [animated]);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[styles.container, animStyle]}>
      <Svg width={size} height={size} viewBox="0 0 100 160" fill="none">
        {/* Bottle cap */}
        <Circle cx="50" cy="15" r="8" fill={color} />
        
        {/* Neck - narrower */}
        <Path
          d="M 42 23 Q 40 30 42 40 L 58 40 Q 60 30 58 23 Z"
          fill={color}
          stroke={color}
          strokeWidth="1"
        />
        
        {/* Shoulder */}
        <Path
          d="M 42 40 Q 30 45 28 60 L 72 60 Q 70 45 58 40 Z"
          fill={color}
          stroke={color}
          strokeWidth="1"
        />
        
        {/* Main body - wider */}
        <Path
          d="M 28 60 Q 20 75 22 110 Q 24 130 35 140 L 65 140 Q 76 130 78 110 Q 80 75 72 60 Z"
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Bottom base */}
        <Path
          d="M 35 140 Q 35 145 40 150 L 60 150 Q 65 145 65 140"
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
        />
        
        {/* Recycling arrow - stylized triangle inside bottle */}
        <Path
          d="M 50 80 L 42 95 L 58 95 Z"
          fill={color}
          opacity="0.5"
        />
      </Svg>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
