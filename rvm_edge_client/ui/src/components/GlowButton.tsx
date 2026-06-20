import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import { Colors, Fonts, FontSizes, Radius, Spacing } from '../constants/theme';

interface Props {
  label: string;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  variant?: 'primary' | 'outline' | 'danger';
  disabled?: boolean;
}

export default function GlowButton({ label, onPress, style, variant = 'primary', disabled = false }: Props) {
  const scale = useSharedValue(1);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95);
  };
  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  if (variant === 'outline') {
    return (
      <Animated.View style={[animStyle, style, disabled && { opacity: 0.5 }]}>
        <TouchableOpacity
          style={styles.outlineBtn}
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          activeOpacity={0.9}
          disabled={disabled}
        >
          <Text style={styles.outlineText}>{label}</Text>
        </TouchableOpacity>
      </Animated.View>
    );
  }

  const gradientColors =
    variant === 'danger'
      ? ([Colors.error, '#B91C1C'] as const)
      : ([Colors.primary, Colors.primaryDark] as const);

  return (
    <Animated.View style={[animStyle, style, disabled && { opacity: 0.5 }]}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.9}
        disabled={disabled}
      >
        <LinearGradient
          colors={gradientColors}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.btn}
        >
          <Text style={styles.label}>{label}</Text>
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  btn: {
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.lg,
    borderRadius: Radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 180,
  },
  label: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.md,
    color: Colors.white,
    letterSpacing: 0.5,
  },
  outlineBtn: {
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.lg,
    borderRadius: Radius.lg,
    borderWidth: 2,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 180,
  },
  outlineText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.md,
    color: Colors.primary,
  },
});
