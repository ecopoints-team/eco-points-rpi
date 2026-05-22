import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, TextInput, ActivityIndicator, TouchableOpacity } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import { useKiosk } from '../context/KioskContext';
import { loginWithQR } from '../api/kioskApi';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function QRScanScreen() {
  const { dispatch } = useKiosk();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanning, setScanning] = useState(true);
  const [manualInput, setManualInput] = useState('');
  const [showManual, setShowManual] = useState(false);
  const scanned = useRef(false);

  const handleBarCodeScanned = async ({ data }: { data: string }) => {
    if (!scanning || scanned.current) return;
    scanned.current = true;
    setScanning(false);

    if (DEV_MODE) {
      const result = await loginWithQR(data);
      if (result.success) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: result.userName } });
      } else {
        dispatch({ type: 'LOGIN_DENIED' });
      }
    } else {
      sendGPIOEvent({ action: 'QR_SCANNED', qr_data: data });
    }
  };

  const handleManualSubmit = () => {
    if (!manualInput.trim()) return;
    handleBarCodeScanned({ data: manualInput.trim() });
  };

  if (!permission?.granted) {
    return (
      <BackgroundGlow style={styles.center}>
        <Text style={styles.title}>Camera Permission Required</Text>
        <GlowButton label="Grant Permission" onPress={requestPermission} />
      </BackgroundGlow>
    );
  }

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <Text style={styles.title}>Scan your EcoPoints QR Code</Text>

      <View style={styles.cameraWrapper}>
        {scanning ? (
          <>
            <CameraView
              style={styles.camera}
              onBarcodeScanned={handleBarCodeScanned}
              barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
            />
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
        <>
          <Text style={styles.hint}>Position your QR code within the frame</Text>

          {!showManual ? (
            <TouchableOpacity style={styles.manualToggle} onPress={() => setShowManual(true)}>
              <Text style={styles.manualToggleText}>Enter code manually</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.manualWrapper}>
              <TextInput
                style={styles.input}
                placeholder="e.g. USER:USER-PU-001"
                placeholderTextColor={Colors.body}
                value={manualInput}
                onChangeText={setManualInput}
                onSubmitEditing={handleManualSubmit}
                autoCapitalize="none"
                autoCorrect={false}
              />
              <View style={styles.manualActions}>
                <TouchableOpacity style={[styles.manualBtn, styles.submitBtn]} onPress={handleManualSubmit}>
                  <Text style={styles.submitText}>Submit</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.manualBtn, styles.cancelBtn]} onPress={() => setShowManual(false)}>
                  <Text style={styles.cancelText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </>
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
  camera: { flex: 1 },
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
  manualToggle: {
    paddingVertical: Spacing.xs,
  },
  manualToggleText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.primaryDark,
    textDecorationLine: 'underline',
  },
  manualWrapper: {
    width: 280,
    gap: Spacing.xs,
    alignItems: 'center',
  },
  input: {
    width: '100%',
    height: 48,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: Colors.primaryLight,
    paddingHorizontal: 12,
    backgroundColor: Colors.white,
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.heading,
  },
  manualActions: {
    flexDirection: 'row',
    width: '100%',
    gap: Spacing.xs,
  },
  manualBtn: {
    flex: 1,
    height: 40,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitBtn: {
    backgroundColor: Colors.primary,
  },
  submitText: {
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.sm,
    color: Colors.white,
  },
  cancelBtn: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.body,
  },
  cancelText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.body,
  },
});
