import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import { Feather } from '@expo/vector-icons';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import { useKiosk } from '../context/KioskContext';
import { getVerificationResult } from '../api/kioskApi';
import { DEV_MODE } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

const NO_ITEMS_TIMEOUT_MS = 60_000;
const ABORT_DISPLAY_MS = 3_000;

export default function VerifyingScreen() {
  const { dispatch } = useKiosk();
  const rotation = useSharedValue(0);
  const pulse = useSharedValue(1);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 2000, easing: Easing.linear }),
      -1,
      false
    );

    pulse.value = withRepeat(
      withSequence(
        withTiming(1.15, { duration: 800, easing: Easing.inOut(Easing.ease) }),
        withTiming(1, { duration: 800, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );

    if (DEV_MODE) {
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
    }
  }, []);

  // 60-second no-items timeout
  useEffect(() => {
    const timeout = setTimeout(() => {
      setTimedOut(true);
    }, NO_ITEMS_TIMEOUT_MS);

    return () => clearTimeout(timeout);
  }, []);

  // After showing timeout message, return to start
  useEffect(() => {
    if (!timedOut) return;
    const abort = setTimeout(() => {
      dispatch({ type: 'SYSTEM_CLEAR' });
    }, ABORT_DISPLAY_MS);
    return () => clearTimeout(abort);
  }, [timedOut]);

  const spinCW = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  const spinCCW = useAnimatedStyle(() => ({
    transform: [{ rotate: `-${rotation.value}deg` }],
  }));

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
    opacity: pulse.value === 1 ? 0.8 : 1,
  }));

  if (timedOut) {
    return (
      <BackgroundGlow style={styles.container}>
        <LogoHeader />
        <Feather name="alert-circle" size={80} color={Colors.error} />
        <Text style={styles.timeoutTitle}>No Items Detected</Text>
        <Text style={styles.timeoutSubtitle}>Aborting Session.</Text>
      </BackgroundGlow>
    );
  }

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      
      <View style={styles.animationContainer}>
        {/* Outer dashed ring rotating clockwise */}
        <Animated.View style={[styles.ring, styles.outerRing, spinCW]} />
        
        {/* Middle solid ring rotating counter-clockwise */}
        <Animated.View style={[styles.ring, styles.middleRing, spinCCW]} />
        
        {/* Inner pulsing circle with icon */}
        <Animated.View style={[styles.innerPulse, pulseStyle]}>
          <Feather name="cpu" size={48} color={Colors.primaryDark} />
        </Animated.View>
      </View>

      <View style={styles.textContainer}>
        <Text style={styles.title}>Verifying your bottles…</Text>
        <Text style={styles.subtitle}>Please wait a moment</Text>
      </View>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.xl },
  animationContainer: {
    width: 220,
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: Spacing.md,
  },
  ring: {
    position: 'absolute',
    borderRadius: 999,
  },
  outerRing: {
    width: 220,
    height: 220,
    borderWidth: 4,
    borderStyle: 'dashed',
    borderColor: Colors.primaryLight,
    opacity: 0.6,
  },
  middleRing: {
    width: 170,
    height: 170,
    borderWidth: 6,
    borderColor: Colors.primary,
    borderTopColor: Colors.accent,
    borderBottomColor: Colors.accent,
    opacity: 0.8,
  },
  innerPulse: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: Colors.bgTint,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 8,
    borderWidth: 2,
    borderColor: Colors.primaryLight,
  },
  textContainer: {
    alignItems: 'center',
    gap: Spacing.sm,
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
    textAlign: 'center',
  },
  // Timeout state
  timeoutTitle: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xxl,
    color: Colors.error,
    textAlign: 'center',
  },
  timeoutSubtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.lg,
    color: Colors.body,
    textAlign: 'center',
  },
});
