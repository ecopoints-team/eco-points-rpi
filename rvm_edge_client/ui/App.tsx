import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import DevPanel from './src/components/DevPanel';
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
import { useGPIOBridge } from './src/hooks/useGPIOBridge';

import StartScreen from './src/screens/StartScreen';
import IdleScreen from './src/screens/IdleScreen';
import QRScanScreen from './src/screens/QRScanScreen';
import ReadyScreen from './src/screens/ReadyScreen';
import VerifyingScreen from './src/screens/VerifyingScreen';
import AcceptedScreen from './src/screens/AcceptedScreen';
import RejectedScreen from './src/screens/RejectedScreen';
import ThankYouScreen from './src/screens/ThankYouScreen';
import BinFullScreen from './src/screens/BinFullScreen';
import DoorOpenScreen from './src/screens/DoorOpenScreen';
import DeniedScreen from './src/screens/DeniedScreen';
import { Colors } from './src/constants/theme';

function KioskRouter() {
  const { screen, dispatch } = useKiosk();

  useKioskTimer(screen, dispatch);
  useGPIOBridge(dispatch);

  let ActiveScreen: React.ReactElement;
  switch (screen) {
    case 'START':      ActiveScreen = <StartScreen />; break;
    case 'IDLE':       ActiveScreen = <IdleScreen />; break;
    case 'QR_SCAN':    ActiveScreen = <QRScanScreen />; break;
    case 'READY':      ActiveScreen = <ReadyScreen />; break;
    case 'VERIFYING':  ActiveScreen = <VerifyingScreen />; break;
    case 'ACCEPTED':   ActiveScreen = <AcceptedScreen />; break;
    case 'REJECTED':   ActiveScreen = <RejectedScreen />; break;
    case 'THANK_YOU':  ActiveScreen = <ThankYouScreen />; break;
    case 'BIN_FULL':   ActiveScreen = <BinFullScreen />; break;
    case 'DOOR_OPEN':  ActiveScreen = <DoorOpenScreen />; break;
    case 'DENIED':     ActiveScreen = <DeniedScreen />; break;
    default:           ActiveScreen = <StartScreen />;
  }

  return (
    <View style={{ flex: 1 }}>
      {ActiveScreen}
      <DevPanel />
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
