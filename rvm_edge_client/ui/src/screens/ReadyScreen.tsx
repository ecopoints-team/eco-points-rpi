import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import RecyclingIcon from '../components/RecyclingIcon';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function ReadyScreen() {
  const { payload, dispatch } = useKiosk();

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      
      <View style={styles.textWrapper}>
        <Text style={styles.welcome}>
          Welcome, {payload.userName ?? 'Recycler'}!
        </Text>
      </View>

      <RecyclingIcon size={120} color={Colors.primary} animated={true} />

      <View style={styles.textWrapper}>
        <Text style={styles.instruction}>
          Please insert plastic bottles to begin.
        </Text>
        <Text style={styles.hint}>
          The machine will scan and verify them automatically.
        </Text>
      </View>

      {/* Main user actions */}
      <View style={styles.actionsContainer}>
        <GlowButton
          label="Cancel"
          variant="outline"
          onPress={() => {
            dispatch({ type: 'SYSTEM_CLEAR' });
            if (!DEV_MODE) {
              sendGPIOEvent({ action: 'CANCEL' });
            }
          }}
          style={styles.btn}
        />
      </View>

      {/* Dev/prototype manual trigger - tucked into bottom right corner */}
      <TouchableOpacity
        style={styles.simButton}
        activeOpacity={0.8}
        onPress={() => {
          dispatch({ type: 'BOTTLE_INSERTED' });
          if (!DEV_MODE) {
            sendGPIOEvent({ action: 'BOTTLE_INSERTED' });
          }
        }}
      >
        <Text style={styles.simButtonText}>Simulate: Bottle Inserted</Text>
      </TouchableOpacity>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  textWrapper: {
    alignItems: 'center',
    gap: Spacing.xs,
  },
  welcome: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.heading,
    textAlign: 'center',
  },
  instruction: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
    marginTop: Spacing.sm,
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.body,
    textAlign: 'center',
  },
  actionsContainer: {
    alignItems: 'center',
    gap: Spacing.sm,
    marginTop: Spacing.md,
  },
  btn: { 
    minWidth: 200,
  },
  simButton: {
    position: 'absolute',
    bottom: Spacing.md,
    right: Spacing.md,
    backgroundColor: 'rgba(6, 78, 59, 0.12)', // Subtle glassmorphic background
    borderColor: 'rgba(6, 78, 59, 0.3)',
    borderWidth: 1,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    zIndex: 100,
  },
  simButtonText: {
    fontFamily: Fonts.mono,
    fontSize: FontSizes.xs - 2, // Extra small text to make it extremely unobtrusive
    color: Colors.primaryDark,
    fontWeight: 'bold',
  },
});

