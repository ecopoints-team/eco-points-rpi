import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TextInput, Keyboard, TouchableOpacity } from 'react-native';
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
  const scanned = useRef(false);
  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    const focusInterval = setInterval(() => {
      if (scanning && inputRef.current) {
        inputRef.current.focus();
      }
    }, 500);
    return () => clearInterval(focusInterval);
  }, [scanning]);

  const handleBarCodeScanned = async (data: string) => {
    if (!scanning || scanned.current) return;
    scanned.current = true;
    setScanning(false);
    Keyboard.dismiss();

    if (DEV_MODE) {
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
          <>
            <TextInput
              ref={inputRef}
              value={inputValue}
              onChangeText={setInputValue}
              onSubmitEditing={onSubmitEditing}
              autoFocus={true}
              showSoftInputOnFocus={false}
              autoCapitalize="none"
              autoCorrect={false}
              style={styles.hiddenInput}
            />
            <View style={styles.scanIndicator}>
              <Text style={styles.scanIndicatorText}>Waiting for Scanner...</Text>
              {inputValue.length > 0 && (
                <View style={{ alignItems: 'center', marginTop: 10 }}>
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
          </>
        ) : (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Verifying QR Code...</Text>
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
  scanIndicatorText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.md,
    color: Colors.primary,
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
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    gap: Spacing.sm,
  },
  loadingText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.md,
    color: Colors.heading,
    textAlign: 'center',
  },
});

