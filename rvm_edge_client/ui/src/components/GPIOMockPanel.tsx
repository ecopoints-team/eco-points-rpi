import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withTiming, Easing } from 'react-native-reanimated';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing } from '../constants/theme';

export default function GPIOMockPanel() {
  const { screen, payload, dispatch } = useKiosk();
  const previousScreen = useRef(screen);

  // State for Door
  const isDoorOpen = screen === 'DOOR_OPEN';

  // Outputs (Indicators)
  const isStrobeOn = screen === 'VERIFYING';
  
  // Orange is only when a user is in a session
  const sessionStates = ['QR_SCAN', 'READY', 'VERIFYING', 'ACCEPTED', 'REJECTED', 'THANK_YOU'];
  const isInProgressOn = sessionStates.includes(screen);
  
  // Fault turns on for bin full or door open
  const isFaultOn = payload.isBinFull || screen === 'BIN_FULL_DENIED' || isDoorOpen;

  // Mock states for the inputs that don't go directly to Kiosk context
  const [homingSensor, setHomingSensor] = useState(true); // true = raised
  const [pulseSteps, setPulseSteps] = useState('1250');
  const [pulseDirection, setPulseDirection] = useState('1'); // 1 = forward (raise), 0 = backward (drop)

  // Animated platform representation
  // 0 deg = vertical (dropped), -90 deg = horizontal (raised)
  const platformAngle = useSharedValue(-90);

  const platformStyle = useAnimatedStyle(() => {
    return {
      transform: [{ rotate: `${platformAngle.value}deg` }],
    };
  });

  const handlePulseMotor = () => {
    const steps = parseInt(pulseSteps, 10);
    const isForward = pulseDirection === '1';
    
    if (isNaN(steps) || steps <= 0) return;

    // Simulate duration based on steps (e.g. 1000 steps = 1000ms)
    const duration = Math.min(steps * 2, 3000); 

    // Animate angle
    // If forward (raise), angle goes to -90 (horizontal)
    // If backward (drop), angle goes to 0 (vertical)
    const targetAngle = isForward ? -90 : 0;
    
    platformAngle.value = withTiming(targetAngle, {
      duration,
      easing: Easing.inOut(Easing.ease)
    });

    // Update homing sensor after duration
    setTimeout(() => {
      setHomingSensor(isForward);
    }, duration);
  };

  // Listen to screen changes to automatically drop and raise the platform on successful verification
  useEffect(() => {
    if (screen === 'ACCEPTED' && previousScreen.current === 'VERIFYING') {
      // Drop the platform (go to 0 deg, vertical)
      platformAngle.value = withTiming(0, {
        duration: 1000,
        easing: Easing.inOut(Easing.ease),
      });
      setTimeout(() => {
        setHomingSensor(false); // false = dropped
        
        // Briefly stay dropped, then raise the platform again
        setTimeout(() => {
          platformAngle.value = withTiming(-90, {
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
          });
          setTimeout(() => {
            setHomingSensor(true); // true = raised
          }, 1000);
        }, 1500);
      }, 1000);
    } else if (screen === 'READY' || screen === 'START') {
      // Ensure the platform is raised for the next session/bottle (go to -90 deg, horizontal)
      platformAngle.value = withTiming(-90, {
        duration: 1000,
        easing: Easing.inOut(Easing.ease),
      });
      setTimeout(() => {
        setHomingSensor(true); // true = raised
      }, 1000);
    }
    previousScreen.current = screen;
  }, [screen]);

  const toggleDoor = () => {
    if (isDoorOpen) {
      dispatch({ type: 'DOOR_CLOSED' });
    } else {
      dispatch({ type: 'SET_DOOR_OPEN' });
    }
  };

  const toggleBin = () => {
    if (payload.isBinFull) {
      dispatch({ type: 'CLEAR_BIN_FULL' });
    } else {
      dispatch({ type: 'SET_BIN_FULL' });
    }
  };

  const Indicator = ({ label, isOn, color }: { label: string; isOn: boolean; color: string }) => (
    <View style={styles.indicatorRow}>
      <View style={[styles.led, { backgroundColor: isOn ? color : '#333' }]} />
      <Text style={styles.indicatorLabel}>{label}</Text>
    </View>
  );

  return (
    <ScrollView style={styles.panel} contentContainerStyle={styles.panelContent} showsVerticalScrollIndicator={false}>
      <Text style={styles.title}>GPIO Mock Panel</Text>

      {/* Outputs Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Outputs (Indicators)</Text>
        <Indicator label="GPIO 27 - Fault (Red)" isOn={isFaultOn} color="#ef4444" />
        <Indicator label="GPIO 26 - In Progress (Orange)" isOn={isInProgressOn} color="#f97316" />
        <Indicator label="GPIO 22 - Strobe (White)" isOn={isStrobeOn} color="#ffffff" />
      </View>

      {/* Inputs Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Inputs (Sensors)</Text>
        <TouchableOpacity style={styles.button} onPress={toggleDoor}>
          <Text style={styles.buttonText}>
            GPIO 11 - Door Switch: {isDoorOpen ? 'OPEN' : 'CLOSED'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={toggleBin}>
          <Text style={styles.buttonText}>
            GPIO 5 - Curtain: {payload.isBinFull ? 'FULL' : 'OK'}
          </Text>
        </TouchableOpacity>
        
        <View style={styles.readOnlyRow}>
          <Text style={styles.indicatorLabel}>GPIO 6 - Homing Sensor (Motor): {homingSensor ? 'TOUCHED (Raised)' : 'OPEN (Dropped)'}</Text>
        </View>
      </View>

      {/* Motor Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Platform Motor Control</Text>
        <View style={styles.inputRow}>
          <Text style={styles.label}>Steps:</Text>
          <TextInput 
            style={styles.input} 
            value={pulseSteps} 
            onChangeText={setPulseSteps} 
            keyboardType="numeric" 
          />
        </View>
        <View style={styles.inputRow}>
          <Text style={styles.label}>Dir (1=up, 0=down):</Text>
          <TextInput 
            style={styles.input} 
            value={pulseDirection} 
            onChangeText={setPulseDirection} 
            keyboardType="numeric" 
            maxLength={1}
          />
        </View>
        <TouchableOpacity style={styles.primaryButton} onPress={handlePulseMotor}>
          <Text style={styles.primaryButtonText}>Simulate PULSE</Text>
        </TouchableOpacity>
        
        {/* Visual Platform Representation */}
        <View style={styles.platformContainer}>
          <Text style={styles.label}>Platform Vis:</Text>
          <View style={styles.platformBox}>
            <Animated.View style={[styles.platformLine, platformStyle]} />
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  panel: {
    width: 300,
    backgroundColor: '#111827',
    borderRightWidth: 1,
    borderRightColor: '#374151',
  },
  panelContent: {
    padding: Spacing.xs,
    paddingBottom: Spacing.xl,
  },
  title: {
    color: '#10b981',
    fontFamily: Fonts.heading,
    fontSize: FontSizes.lg,
    marginBottom: Spacing.lg,
    textAlign: 'center',
  },
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    color: Colors.primaryLight,
    fontFamily: Fonts.heading,
    fontSize: FontSizes.md,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
    paddingBottom: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  indicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  led: {
    width: 16,
    height: 16,
    borderRadius: 8,
    marginRight: Spacing.sm,
    borderWidth: 1,
    borderColor: '#4b5563',
  },
  indicatorLabel: {
    color: '#d1d5db',
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
  },
  readOnlyRow: {
    paddingVertical: Spacing.xs,
  },
  button: {
    backgroundColor: '#374151',
    padding: Spacing.sm,
    borderRadius: 4,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: '#4b5563',
  },
  buttonText: {
    color: '#f3f4f6',
    fontFamily: Fonts.mono,
    fontSize: FontSizes.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
    justifyContent: 'space-between',
  },
  label: {
    color: '#d1d5db',
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
  },
  input: {
    backgroundColor: '#1f2937',
    color: '#fff',
    fontFamily: Fonts.mono,
    padding: Spacing.xs,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#4b5563',
    width: 80,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: Colors.primary,
    padding: Spacing.sm,
    borderRadius: 4,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  primaryButtonText: {
    color: Colors.white,
    fontFamily: Fonts.bodyBold,
    fontSize: FontSizes.sm,
  },
  platformContainer: {
    marginTop: Spacing.lg,
    alignItems: 'center',
  },
  platformBox: {
    width: 100,
    height: 100,
    borderWidth: 1,
    borderColor: '#374151',
    marginTop: Spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f2937',
    overflow: 'hidden',
  },
  platformLine: {
    width: 6,
    height: 80,
    backgroundColor: '#10b981',
    borderRadius: 3,
  },
});
