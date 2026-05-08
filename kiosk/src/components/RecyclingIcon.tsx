import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface Props {
  size?: number;
  color?: string;
  animated?: boolean;
}

export default function RecyclingIcon({ size = 80, color = '#10B981', animated = true }: Props) {
  const rotation = useSharedValue(0);

  useEffect(() => {
    if (animated) {
      rotation.value = withRepeat(
        withTiming(360, { duration: 12000, easing: Easing.linear }),
        -1,
        false
      );
    }
  }, [animated]);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <Animated.View style={[styles.container, animStyle]}>
      <MaterialCommunityIcons name="recycle" size={size} color={color} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
