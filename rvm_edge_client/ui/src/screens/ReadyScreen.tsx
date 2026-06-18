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
          Please insert bottles in place.
        </Text>
        <Text style={styles.hint}>
          The machine will scan and verify them automatically.
        </Text>
      </View>

      {/* Main user actions */}
      <View style={styles.actionsContainer}>
        {DEV_MODE && (
          <GlowButton
            label="Manual: Bottle Inserted & Door Closed"
            variant="primary"
            onPress={() => {
              dispatch({ type: 'BOTTLE_INSERTED' });
              if (!DEV_MODE) {
                sendGPIOEvent({ action: 'BOTTLE_INSERTED' });
              }
            }}
            style={[styles.btn, { minWidth: 400, paddingVertical: 20 }]}
          />
        )}
        
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
});

