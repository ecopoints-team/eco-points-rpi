import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import { useKiosk, KioskState } from '../context/KioskContext';
import { Colors, Fonts, FontSizes } from '../constants/theme';

const SCREENS: { label: string; screen: KioskState }[] = [
  { label: '1 Start',       screen: 'START' },
  { label: '2 QR Scan',     screen: 'QR_SCAN' },
  { label: '3 Ready',       screen: 'READY' },
  { label: '4 Verifying',   screen: 'VERIFYING' },
  { label: '5 Accepted',    screen: 'ACCEPTED' },
  { label: '6 Rejected',    screen: 'REJECTED' },
  { label: '7 Thank You',   screen: 'THANK_YOU' },
  { label: '8 Door Open',   screen: 'DOOR_OPEN' },
  { label: '9 Denied',     screen: 'DENIED' },
  { label: '10 Admin Menu', screen: 'ADMIN_MENU' },
  { label: '11 Admin Act',  screen: 'ADMIN_ACTION' },
  { label: '12 Admin Note', screen: 'ADMIN_NOTES' },
  { label: '13 Bin Denied', screen: 'BIN_FULL_DENIED' },
];

// Fake payload so result screens render correctly
const MOCK_PAYLOAD = {
  userName: 'Jay Dizon',
  points: 15,
  bottleCount: 3,
  reason: 'Non-recyclable material detected.',
};

export default function DevPanel() {
  const { screen: current, payload, dispatch } = useKiosk();
  const [isOpen, setIsOpen] = useState(false);

  if (!isOpen) {
    return (
      <Pressable
        style={styles.hoverTarget}
        onHoverIn={() => setIsOpen(true)}
        onPress={() => setIsOpen(true)}
      />
    );
  }

  return (
    <View 
      style={styles.wrapper} 
      pointerEvents="box-none"
    >
      {/* Indicator tab */}
      <TouchableOpacity style={styles.tab} onPress={() => setIsOpen(false)}>
        <Text style={styles.tabText}>▼ DEV MODE ACTIVE (Tap to hide) | Bin: {payload.isBinFull ? '🔴 FULL' : '🟢 OK'}</Text>
      </TouchableOpacity>

      <ScrollView
        horizontal
        style={styles.panel}
        contentContainerStyle={styles.row}
        showsHorizontalScrollIndicator={false}
      >
        {/* Bin Full Toggle */}
        <TouchableOpacity
          style={[styles.btn, styles.toggleBtn]}
          onPress={() => {
            if (payload.isBinFull) {
              dispatch({ type: 'CLEAR_BIN_FULL' });
            } else {
              dispatch({ type: 'SET_BIN_FULL' });
            }
          }}
        >
          <Text style={[styles.btnText, styles.toggleText]}>
            {payload.isBinFull ? '🗑 Clear Bin' : '🗑 Set Bin Full'}
          </Text>
        </TouchableOpacity>

        {SCREENS.map(({ label, screen }) => (
          <TouchableOpacity
            key={screen}
            style={[styles.btn, current === screen && styles.btnActive]}
            onPress={() => {
              // Inject mock payload then jump to state
              if (screen === 'READY' || screen === 'VERIFYING') {
                dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: MOCK_PAYLOAD.userName } });
              }
              if (screen === 'ACCEPTED') {
                dispatch({ type: 'LOGIN_SUCCESS', payload: { userName: MOCK_PAYLOAD.userName } });
                dispatch({ type: 'VERIFY_SUCCESS', payload: { points: MOCK_PAYLOAD.points, bottleCount: MOCK_PAYLOAD.bottleCount } });
                return;
              }
              if (screen === 'REJECTED') {
                dispatch({ type: 'VERIFY_FAIL', payload: { reason: MOCK_PAYLOAD.reason } });
                return;
              }
              if (screen === 'DENIED')          { dispatch({ type: 'LOGIN_DENIED' }); return; }
              if (screen === 'DOOR_OPEN')       { dispatch({ type: 'SET_DOOR_OPEN' }); return; }
              if (screen === 'IDLE')            { dispatch({ type: 'GO_IDLE' }); return; }
              if (screen === 'START')           { dispatch({ type: 'SYSTEM_CLEAR' }); return; }
              if (screen === 'THANK_YOU')       { dispatch({ type: 'ADVANCE_THANK_YOU' }); return; }
              if (screen === 'QR_SCAN')         { dispatch({ type: 'WAKE' }); return; }
              if (screen === 'ADMIN_MENU')      { dispatch({ type: 'ADMIN_LOGIN', payload: { userName: 'Admin' } }); return; }
              if (screen === 'ADMIN_ACTION')    { dispatch({ type: 'ADMIN_LOGIN', payload: { userName: 'Admin' } }); dispatch({ type: 'ADMIN_SELECT_CATEGORY', payload: { category: 'maintenance' } }); return; }
              if (screen === 'ADMIN_NOTES')     { dispatch({ type: 'ADMIN_LOGIN', payload: { userName: 'Admin' } }); dispatch({ type: 'ADMIN_SELECT_CATEGORY', payload: { category: 'maintenance' } }); dispatch({ type: 'ADMIN_SELECT_ACTION', payload: { action: 'Sensor Error' } }); return; }
              if (screen === 'BIN_FULL_DENIED') { dispatch({ type: 'BIN_FULL_USER_DENIED' }); return; }
            }}
          >
            <Text style={[styles.btnText, current === screen && styles.btnTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  hoverTarget: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    width: 60,
    height: 60,
    zIndex: 9999,
  },
  wrapper: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
  },
  tab: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.heading,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderTopRightRadius: 8,
  },
  tabText: {
    fontFamily: Fonts.mono,
    fontSize: FontSizes.xs,
    color: Colors.primaryLight,
  },
  panel: {
    backgroundColor: 'rgba(6,78,59,0.92)',
    borderTopWidth: 1,
    borderTopColor: Colors.primary,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 6,
    gap: 6,
  },
  btn: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.primaryLight,
  },
  btnActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  btnText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.xs,
    color: Colors.primaryLight,
  },
  btnTextActive: {
    color: Colors.white,
    fontFamily: Fonts.bodyBold,
  },
  toggleBtn: {
    borderColor: Colors.accent,
    backgroundColor: 'rgba(251, 191, 36, 0.15)',
  },
  toggleText: {
    color: Colors.accent,
    fontFamily: Fonts.bodyBold,
  },
});
