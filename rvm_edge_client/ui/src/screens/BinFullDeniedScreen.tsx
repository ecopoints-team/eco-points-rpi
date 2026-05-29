import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import LogoHeader from '../components/LogoHeader';
import StatusBadge from '../components/StatusBadge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function BinFullDeniedScreen() {
  return (
    <LinearGradient
      colors={[Colors.accentLight, '#FDE68A', Colors.accentLight]}
      style={styles.container}
    >
      <LogoHeader />
      <StatusBadge label="MACHINE FULL" variant="warning" />
      <Text style={styles.title}>
        Sorry, the machine is currently full.
      </Text>
      <Text style={styles.body}>
        Please Try Again Later.
      </Text>
      <Text style={styles.hint}>
        Returning to welcome screen shortly…
      </Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
    overflow: 'hidden',
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: '#92400E',
    textAlign: 'center',
    maxWidth: 500,
  },
  body: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.xl,
    color: '#78350F',
    textAlign: 'center',
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: '#78350F',
    marginTop: Spacing.sm,
    opacity: 0.6,
  },
});
