import React from 'react';
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import StatusBadge from '../components/StatusBadge';
import LogoHeader from '../components/LogoHeader';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function BinFullScreen() {
  const { dispatch } = useKiosk();

  return (
    <TouchableOpacity
      style={{ flex: 1 }}
      activeOpacity={1}
      onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
    >
      <LinearGradient
        colors={[Colors.accentLight, '#FDE68A', Colors.accentLight]}
        style={styles.container}
      >
        <LogoHeader />
        <StatusBadge label="OUT OF SERVICE" variant="warning" />
        <Text style={styles.title}>Collection Bin is Full</Text>
        <Text style={styles.body}>
          Please contact staff to empty the bin.{'\n'}
          The machine will resume automatically once resolved.
        </Text>
        <Text style={styles.tap}>Tap anywhere to return to start</Text>
      </LinearGradient>
    </TouchableOpacity>
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
  },
  body: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: '#78350F',
    textAlign: 'center',
    lineHeight: FontSizes.lg * 1.6,
  },
  tap: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: '#78350F',
    marginTop: Spacing.sm,
    opacity: 0.6,
  },
});
