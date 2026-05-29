import React, { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedProps,
  withTiming,
  Easing,
  runOnJS,
} from 'react-native-reanimated';
import { Colors, Fonts, FontSizes } from '../constants/theme';

interface Props {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
}

export default function PointsDisplay({
  value,
  duration = 1500,
  prefix = '+',
  suffix = ' pts',
}: Props) {
  const animValue = useSharedValue(0);
  const [display, setDisplay] = React.useState(0);

  useEffect(() => {
    animValue.value = withTiming(value, {
      duration,
      easing: Easing.out(Easing.cubic),
    });
  }, [value]);

  // Drive display via JS-side interval for web compatibility
  useEffect(() => {
    const start = Date.now();
    const tick = setInterval(() => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.floor(eased * value));
      if (progress >= 1) clearInterval(tick);
    }, 16);
    return () => clearInterval(tick);
  }, [value, duration]);

  return (
    <View style={styles.container}>
      <Text style={styles.value}>
        {prefix}
        {display}
        {suffix}
      </Text>
      <Text style={styles.label}>EcoPoints Earned</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  value: {
    fontFamily: Fonts.mono,
    fontSize: FontSizes.hero,
    color: Colors.primary,
    letterSpacing: 2,
  },
  label: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    marginTop: 4,
    letterSpacing: 1,
  },
});
