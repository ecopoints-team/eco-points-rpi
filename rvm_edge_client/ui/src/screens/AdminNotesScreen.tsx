import React, { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing, scale, vscale } from '../constants/theme';

const QUICK_NOTES = [
  'Issues Resolved',
  'Bin Cleared',
  'Needs Further Review',
  'Maintenance Complete',
];

export default function AdminNotesScreen() {
  const { payload, dispatch } = useKiosk();
  const [selectedNotes, setSelectedNotes] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleToggle = (note: string) => {
    setSelectedNotes((prev) =>
      prev.includes(note)
        ? prev.filter((n) => n !== note)
        : [...prev, note]
    );
  };

  const handleConfirm = async () => {
    if (isSubmitting || selectedNotes.length === 0) return;
    setIsSubmitting(true);
    
    const actionType = payload.adminAction ?? 'Unknown Action';
    const notesString = selectedNotes.join(', ');
    const status = selectedNotes.includes('Needs Further Review') ? 'Pending' : 'Resolved';

    sendGPIOEvent({
      action: 'SUBMIT_LOG',
      payload: {
        actionType,
        status,
        notes: notesString,
      }
    });
    
    // Slight delay to allow WebSocket message to process before clearing
    setTimeout(() => {
      dispatch({ type: 'ADMIN_COMPLETE' });
      if (!DEV_MODE) sendGPIOEvent({ action: 'SYSTEM_CLEAR' });
    }, 300);
  };

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <StatusBadge label="ADMIN MODE" variant="warning" />

      <Text style={styles.title}>{payload.adminAction ?? 'Action'}</Text>
      <Text style={styles.subtitle}>Select all notes that apply</Text>

      <View style={styles.optionsList}>
        {QUICK_NOTES.map((note) => {
          const isSelected = selectedNotes.includes(note);
          return (
            <GlowButton
              key={note}
              label={note}
              variant={isSelected ? 'primary' : 'outline'}
              onPress={() => handleToggle(note)}
              style={styles.optionBtn}
            />
          );
        })}
      </View>

      <View style={styles.buttonRow}>
        <GlowButton
          label="Back"
          variant="outline"
          disabled={isSubmitting}
          onPress={() => dispatch({ type: 'ADMIN_BACK' })}
          style={styles.btn}
        />
        <GlowButton
          label="Enter/Confirm"
          disabled={isSubmitting || selectedNotes.length === 0}
          onPress={handleConfirm}
          style={styles.btn}
        />
      </View>
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: vscale(6),
    paddingVertical: vscale(20),
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.lg,
    color: Colors.heading,
    textAlign: 'center',
    marginTop: vscale(10),
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.body,
    textAlign: 'center',
  },
  optionsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: Spacing.sm,
    marginVertical: vscale(20),
    width: '90%',
    maxWidth: scale(500),
  },
  optionBtn: {
    minWidth: scale(220),
    flexGrow: 0,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: vscale(10),
  },
  btn: {
    minWidth: scale(140),
  },
});
