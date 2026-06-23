import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, Keyboard, TouchableOpacity } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { loginWithQR } from '../api/kioskApi';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function QRScanScreen() {
  const { dispatch } = useKiosk();
  const [scanning, setScanning] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const scanned = useRef(false);
  const inputRef = useRef<TextInput>(null);

  const rotation = useSharedValue(0);

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 1200, easing: Easing.linear }),
      -1,
      false
    );
  }, []);

  const spinStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  useEffect(() => {
    const focusInterval = setInterval(() => {
      if (scanning && inputRef.current && !isFocused) {
        inputRef.current.focus();
      }
    }, 1000);
    return () => clearInterval(focusInterval);
  }, [scanning, isFocused]);

  const handleBarCodeScanned = async (data: string) => {
    if (!scanning || scanned.current) return;
    scanned.current = true;
    setScanning(false);
    Keyboard.dismiss();

    if (DEV_MODE) {
      // DEV_MODE only: mock auth — not active in production (DEV_MODE=false)
      const result = await loginWithQR(data);
      if (result.success) {
        if (result.role && ['technician', 'superadmin', 'head_admin'].includes(result.role)) {
          dispatch({ type: 'ADMIN_LOGIN', payload: { userName: result.userName } });
        } else {
          dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: result.userName } });
        }
      } else {
        dispatch({ type: 'LOGIN_DENIED' });
      }
    } else {
      // Production path: routes QR data to firmware via WebSocket
      sendGPIOEvent({ action: 'QR_SCANNED', qr_data: data });
    }
  };

  const onSubmitEditing = () => {
    if (inputValue.trim()) {
      handleBarCodeScanned(inputValue.trim());
    }
  };

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <Text style={styles.title}>Show your QR Code</Text>
      <Text style={styles.hint}>QR Scanner Activated</Text>

      <View style={styles.cameraWrapper}>
        {scanning ? (
          <TouchableOpacity 
            activeOpacity={1} 
            onPress={() => inputRef.current?.focus()}
            style={{ flex: 1 }}
          >
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
            <View style={styles.scanIndicator}>
              {isFocused ? (
                <>
                  <Text style={styles.scanIndicatorTextReady}>Scanner Ready</Text>
                  <Text style={styles.scanIndicatorSubtext}>Position code within frame</Text>
                </>
              ) : (
                <>
                  <Text style={styles.scanIndicatorTextInactive}>Scanner Inactive</Text>
                  <Text style={styles.scanIndicatorSubtextInactive}>Tap anywhere to reactivate</Text>
                </>
              )}
              {inputValue.length > 0 && (
                <View style={{ alignItems: 'center', marginTop: 16 }}>
                  <Text style={styles.debugText}>Scanned: {inputValue}</Text>
                  <TouchableOpacity onPress={onSubmitEditing} style={styles.manualSubmitBtn}>
                    <Text style={styles.manualSubmitText}>Submit Scan</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
            {/* Reticle corners */}
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </TouchableOpacity>
        ) : (
          <View style={styles.loadingOverlay}>
            <Animated.View style={[styles.spinner, spinStyle]} />
            <Text style={styles.loadingText}>Verifying QR Code...</Text>
            <Text style={styles.loadingSubtext}>Please wait</Text>
          </View>
        )}
      </View>

      {scanning && (
        <Text style={styles.hint}>Position your QR code within the frame</Text>
      )}

      <GlowButton
        label="Cancel Session"
        variant="outline"
        onPress={() => {
          dispatch({ type: 'SYSTEM_CLEAR' });
          if (!DEV_MODE) {
            sendGPIOEvent({ action: 'CANCEL' });
          }
        }}
      />
    </BackgroundGlow>
  );
}

const CORNER = 24;
const BORDER = 4;

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  center: { alignItems: 'center', justifyContent: 'center', gap: Spacing.lg },
  title: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
  },
  cameraWrapper: {
    width: 280,
    height: 280,
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#000000',
  },
  hiddenInput: {
    position: 'absolute',
    width: 1,
    height: 1,
    opacity: 0,
  },
  scanIndicator: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanIndicatorTextReady: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: Colors.primary,
    textAlign: 'center',
  },
  scanIndicatorTextInactive: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.xl,
    color: '#EF4444',
    textAlign: 'center',
  },
  scanIndicatorSubtext: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  scanIndicatorSubtextInactive: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: 'rgba(239, 68, 68, 0.7)',
    textAlign: 'center',
  },
  debugText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: '#10B981',
    marginTop: Spacing.sm,
  },
  manualSubmitBtn: {
    marginTop: Spacing.sm,
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 8,
  },
  manualSubmitText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.sm,
    color: '#FFFFFF',
  },
  hint: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
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
  loadingOverlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    gap: Spacing.sm,
  },
  spinner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 4,
    borderColor: Colors.bgTint,
    borderTopColor: Colors.primary,
    marginBottom: Spacing.sm,
  },
  loadingText: {
    fontFamily: Fonts.heading,
    fontSize: FontSizes.lg,
    color: Colors.heading,
    textAlign: 'center',
  },
  loadingSubtext: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    textAlign: 'center',
  },
});

