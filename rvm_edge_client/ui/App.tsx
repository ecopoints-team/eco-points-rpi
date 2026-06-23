import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import DevPanel from './src/components/DevPanel';
import LightIndicator from './src/components/LightIndicator';
import {
  useFonts,
  Fredoka_400Regular,
  Fredoka_600SemiBold,
} from '@expo-google-fonts/fredoka';
import {
  Quicksand_500Medium,
  Quicksand_700Bold,
} from '@expo-google-fonts/quicksand';
import { SpaceMono_400Regular } from '@expo-google-fonts/space-mono';

import { KioskProvider, useKiosk } from './src/context/KioskContext';
import { useKioskTimer } from './src/hooks/useKioskTimer';
import { DEV_MODE, useGPIOBridge } from './src/hooks/useGPIOBridge';

import StartScreen from './src/screens/StartScreen';
import QRScanScreen from './src/screens/QRScanScreen';
import ReadyScreen from './src/screens/ReadyScreen';
import VerifyingScreen from './src/screens/VerifyingScreen';
import AcceptedScreen from './src/screens/AcceptedScreen';
import RejectedScreen from './src/screens/RejectedScreen';
import ThankYouScreen from './src/screens/ThankYouScreen';
import DoorOpenScreen from './src/screens/DoorOpenScreen';
import DeniedScreen from './src/screens/DeniedScreen';
import AdminMenuScreen from './src/screens/AdminMenuScreen';
import AdminActionScreen from './src/screens/AdminActionScreen';
import AdminNotesScreen from './src/screens/AdminNotesScreen';
import BinFullDeniedScreen from './src/screens/BinFullDeniedScreen';
import { Colors } from './src/constants/theme';

function KioskRouter() {
  const { screen, dispatch } = useKiosk();

  useKioskTimer(screen, dispatch);
  useGPIOBridge(dispatch);

  let ActiveScreen: React.ReactElement;
  switch (screen) {
    case 'START':
    case 'IDLE':            ActiveScreen = <StartScreen />; break;
    case 'QR_SCAN':         ActiveScreen = <QRScanScreen />; break;
    case 'READY':           ActiveScreen = <ReadyScreen />; break;
    case 'VERIFYING':       ActiveScreen = <VerifyingScreen />; break;
    case 'ACCEPTED':        ActiveScreen = <AcceptedScreen />; break;
    case 'REJECTED':        ActiveScreen = <RejectedScreen />; break;
    case 'THANK_YOU':       ActiveScreen = <ThankYouScreen />; break;
    case 'DOOR_OPEN':       ActiveScreen = <DoorOpenScreen />; break;
    case 'DENIED':          ActiveScreen = <DeniedScreen />; break;
    case 'ADMIN_MENU':      ActiveScreen = <AdminMenuScreen />; break;
    case 'ADMIN_ACTION':    ActiveScreen = <AdminActionScreen />; break;
    case 'ADMIN_NOTES':     ActiveScreen = <AdminNotesScreen />; break;
    case 'BIN_FULL_DENIED': ActiveScreen = <BinFullDeniedScreen />; break;
    default:                ActiveScreen = <StartScreen />;
  }

  return (
    <View style={{ flex: 1 }}>
      {ActiveScreen}
      {/* <LightIndicator /> */}
      {DEV_MODE && <DevPanel />}
    </View>
  );
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Fredoka_400Regular,
    Fredoka_600SemiBold,
    Quicksand_500Medium,
    Quicksand_700Bold,
    SpaceMono_400Regular,
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <KioskProvider>
      <KioskRouter />
    </KioskProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.bg,
  },
});
