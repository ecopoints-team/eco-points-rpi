import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, Keyboard, TouchableOpacity } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { Feather } from '@expo/vector-icons';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { loginWithQR } from '../api/kioskApi';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

type ScanState = 'idle' | 'loading' | 'success' | 'failure';

export default function QRScanScreen() {
  const { dispatch } = useKiosk();
  const [scanState, setScanState] = useState<ScanState>('idle');
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const scanned = useRef(false);
  const inputRef = useRef<TextInput>(null);

  const rotation = useSharedValue(0);
  const pulse = useSharedValue(1);

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 1200, easing: Easing.linear }),
      -1,
      false
    );
    pulse.value = withRepeat(
      withTiming(1.08, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
      -1,
      true
    );
  }, []);

  const spinStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
  }));

  useEffect(() => {
    const focusInterval = setInterval(() => {
      if (scanState === 'idle' && inputRef.current && !isFocused) {
        inputRef.current.focus();
      }
    }, 1000);
    return () => clearInterval(focusInterval);
  }, [scanState, isFocused]);

  const handleBarCodeScanned = async (data: string) => {
    if (scanState !== 'idle' || scanned.current) return;
    scanned.current = true;
    setScanState('loading');
    Keyboard.dismiss();

    if (DEV_MODE) {
      const result = await loginWithQR(data);
      if (result.success) {
        setScanState('success');
        setTimeout(() => {
          if (result.role && ['technician', 'superadmin', 'head_admin'].includes(result.role)) {
            dispatch({ type: 'ADMIN_LOGIN', payload: { userName: result.userName } });
          } else {
            dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: result.userName } });
          }
        }, 1500);
      } else {
        setScanState('failure');
      }
    } else {
      sendGPIOEvent({ action: 'QR_SCANNED', qr_data: data });
    }
  };

  const onSubmitEditing = () => {
    if (inputValue.trim()) {
      handleBarCodeScanned(inputValue.trim());
    }
  };

  const resetScan = () => {
    setScanState('idle');
    setInputValue('');
    scanned.current = false;
    setTimeout(() => {
      inputRef.current?.focus();
    }, 300);
  };

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <Text style={styles.title}>Show your QR Code</Text>

      <View style={styles.cameraWrapper}>
        <TextInput
          ref={inputRef}
          value={inputValue}
          onChangeText={setInputValue}
          onSubmitEditing={onSubmitEditing}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          autoFocus={true}
          showSoftInputOnFocus={false}
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.hiddenInput}
        />

        {scanState === 'idle' && (
          <TouchableOpacity 
            activeOpacity={1} 
            onPress={() => inputRef.current?.focus()}
            style={{ flex: 1, width: '100%', height: '100%' }}
          >
            <Animated.View style={[StyleSheet.absoluteFill, pulseStyle]}>
              <View style={[styles.corner, styles.topLeft]} />
              <View style={[styles.corner, styles.topRight]} />
              <View style={[styles.corner, styles.bottomLeft]} />
              <View style={[styles.corner, styles.bottomRight]} />
            </Animated.View>
          </TouchableOpacity>
        )}

        {scanState === 'loading' && (
          <View style={styles.stateOverlay}>
            <Animated.View style={[styles.spinner, spinStyle]} />
            <Text style={styles.stateText}>Verifying...</Text>
          </View>
        )}

        {scanState === 'success' && (
          <View style={styles.stateOverlay}>
            <View style={styles.iconCircleSuccess}>
              <Feather name="check" size={48} color="#10B981" />
            </View>
            <Text style={styles.stateTextSuccess}>Verified!</Text>
          </View>
        )}

        {scanState === 'failure' && (
          <View style={styles.stateOverlay}>
            <View style={styles.iconCircleFailure}>
              <Feather name="x" size={48} color="#EF4444" />
            </View>
            <Text style={styles.stateTextFailure}>Invalid QR Code</Text>
            <TouchableOpacity onPress={resetScan} style={styles.retryBtn}>
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {scanState === 'idle' && (
        <Text style={styles.hint}>Position your QR code within the frame</Text>
      )}

      {scanState !== 'success' && (
        <View style={{ marginTop: Spacing.xl }}>
          <GlowButton
            label={scanState === 'failure' ? "Go Back" : "Cancel Session"}
            variant="outline"
            onPress={() => {
              dispatch({ type: 'SYSTEM_CLEAR' });
              if (!DEV_MODE) {
                sendGPIOEvent({ action: 'CANCEL' });
              }
            }}
          />
        </View>
      )}
    </BackgroundGlow>
  );
}

const CORNER = 40;
const BORDER = 6;

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  title: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
    marginBottom: Spacing.md,
  },
  cameraWrapper: {
    width: 280,
    height: 280,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  hiddenInput: {
    position: 'absolute',
    width: 1,
    height: 1,
    opacity: 0,
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    marginTop: Spacing.lg,
  },
  corner: {
    position: 'absolute',
    width: CORNER,
    height: CORNER,
    borderColor: Colors.primary,
  },
  topLeft: { top: 0, left: 0, borderTopWidth: BORDER, borderLeftWidth: BORDER },
  topRight: { top: 0, right: 0, borderTopWidth: BORDER, borderRightWidth: BORDER },
  bottomLeft: { bottom: 0, left: 0, borderBottomWidth: BORDER, borderLeftWidth: BORDER },
  bottomRight: { bottom: 0, right: 0, borderBottomWidth: BORDER, borderRightWidth: BORDER },
  stateOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  spinner: {
    width: 70,
    height: 70,
    borderRadius: 35,
    borderWidth: 4,
    borderColor: 'rgba(16, 185, 129, 0.2)',
    borderTopColor: '#10B981',
    marginBottom: Spacing.sm,
  },
  stateText: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.lg,
    color: '#10B981',
    textAlign: 'center',
  },
  iconCircleSuccess: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.xs,
  },
  stateTextSuccess: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: '#10B981',
  },
  iconCircleFailure: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.xs,
  },
  stateTextFailure: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: '#EF4444',
  },
  retryBtn: {
    marginTop: Spacing.md,
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  retryText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.md,
    color: '#EF4444',
  },
});

