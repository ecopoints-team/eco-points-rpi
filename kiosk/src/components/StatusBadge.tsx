import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Fonts, FontSizes, Radius, Spacing } from '../constants/theme';

type Variant = 'success' | 'warning' | 'error' | 'info';

interface Props {
  label: string;
  variant?: Variant;
}

const BG: Record<Variant, string> = {
  success: '#D1FAE5',
  warning: Colors.accentLight,
  error: Colors.errorLight,
  info: '#DBEAFE',
};

const FG: Record<Variant, string> = {
  success: Colors.primaryDark,
  warning: '#92400E',
  error: '#991B1B',
  info: '#1E40AF',
};

export default function StatusBadge({ label, variant = 'info' }: Props) {
  return (
    <View style={[styles.badge, { backgroundColor: BG[variant] }]}>
      <Text style={[styles.text, { color: FG[variant] }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs / 2,
    borderRadius: Radius.full,
    alignSelf: 'center',
  },
  text: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.sm,
    letterSpacing: 0.5,
  },
});
