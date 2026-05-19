import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import { useKiosk } from '../context/KioskContext';
import { getVerificationResult } from '../api/kioskApi';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function VerifyingScreen() {
  const { dispatch } = useKiosk();
  const rotation = useSharedValue(0);

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 1200, easing: Easing.linear }),
      -1,
      false
    );

    getVerificationResult().then((res) => {
      if (res.accepted) {
        dispatch({
          type: 'VERIFY_SUCCESS',
          payload: { points: res.points, bottleCount: res.bottleCount },
        });
      } else {
        dispatch({
          type: 'VERIFY_FAIL',
          payload: { reason: res.reason ?? 'Unknown error' },
        });
      }
    });
  }, []);

  const spinStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <Animated.View style={[styles.spinner, spinStyle]} />
      <Text style={styles.title}>Verifying your bottles…</Text>
      <Text style={styles.subtitle}>Please wait a moment</Text>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.lg },
  spinner: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 6,
    borderColor: Colors.bgTint,
    borderTopColor: Colors.primary,
  },
  title: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xxl,
    color: Colors.heading,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.body,
  },
});
