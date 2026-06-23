import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import RecyclingIcon from '../components/RecyclingIcon';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, scale, vscale } from '../constants/theme';

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

      <RecyclingIcon size={100} color={Colors.primary} animated={true} />

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
        {/* Hardware GPIO handles bottle insertion now */}
        <GlowButton
          label="Cancel"
          variant="outline"
          onPress={() => {
            dispatch({ type: 'SYSTEM_CLEAR' });
            if (!DEV_MODE) {
              sendGPIOEvent({ action: 'CANCEL' });
            }
          }}
          style={[styles.btn, { minWidth: scale(150) }]}
        />
      </View>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: vscale(12),
    paddingTop: vscale(40),
    paddingBottom: vscale(20),
  },
  textWrapper: {
    alignItems: 'center',
    gap: vscale(4),
  },
  welcome: {
    fontFamily: Fonts.headingBold,
    fontSize: scale(38),
    color: Colors.heading,
    textAlign: 'center',
  },
  instruction: {
    fontFamily: Fonts.bodyBold,
    fontSize: scale(28),
    color: Colors.heading,
    textAlign: 'center',
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: scale(20),
    color: Colors.body,
    textAlign: 'center',
  },
  actionsContainer: {
    alignItems: 'center',
    gap: vscale(10),
    marginTop: vscale(10),
  },
  btn: {
    minWidth: scale(200),
  },
});

