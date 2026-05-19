import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function ReadyScreen() {
  const { payload, dispatch } = useKiosk();

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <Text style={styles.welcome}>
        Welcome, {payload.userName ?? 'Recycler'}!
      </Text>
      <Text style={styles.instruction}>
        Please place plastic bottles on the platform.
      </Text>
      <Text style={styles.hint}>
        The machine will scan and verify them automatically.
      </Text>

      {/* Dev/prototype manual trigger */}
      <GlowButton
        label="Simulate: Bottle Inserted"
        onPress={() => dispatch({ type: 'BOTTLE_INSERTED' })}
        style={styles.btn}
      />
      <GlowButton
        label="Cancel"
        variant="outline"
        onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
        style={styles.btn}
      />
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  welcome: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.heading,
    textAlign: 'center',
  },
  icon: { fontSize: 80 },
  instruction: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    textAlign: 'center',
  },
  btn: { marginTop: Spacing.xs },
});
