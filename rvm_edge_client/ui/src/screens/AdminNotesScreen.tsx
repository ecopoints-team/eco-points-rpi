import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { DEV_MODE, sendGPIOEvent } from '../hooks/useGPIOBridge';
import { Colors, Fonts, FontSizes, Spacing, Radius, scale, vscale } from '../constants/theme';

const QUICK_NOTES = [
  'Issues Resolved',
  'Bin Cleared',
  'Needs Further Review',
  'Maintenance Complete',
];

export default function AdminNotesScreen() {
  const { payload, dispatch } = useKiosk();
  const [notes, setNotes] = useState('');

  const handleQuickNote = (note: string) => {
    setNotes((prev: string) => (prev ? `${prev}\n${note}` : note));
  };

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (status: string) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    
    const actionType = payload.adminAction ?? 'Unknown Action';
    sendGPIOEvent({
      action: 'SUBMIT_LOG',
      payload: {
        actionType,
        status,
        notes,
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
      <Text style={styles.subtitle}>Add notes for this action</Text>

      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.textInput}
          placeholder="Enter maintenance notes..."
          placeholderTextColor={Colors.body}
          value={notes}
          onChangeText={setNotes}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />
      </View>

      <View style={styles.quickNotes}>
        {QUICK_NOTES.map((note) => (
          <TouchableOpacity
            key={note}
            style={styles.quickNoteChip}
            onPress={() => handleQuickNote(note)}
            activeOpacity={0.7}
          >
            <Text style={styles.quickNoteText}>{note}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.buttonRow}>
        <GlowButton
          label="Resolved"
          disabled={isSubmitting}
          onPress={() => handleSubmit('Resolved')}
          style={styles.btn}
        />
        <GlowButton
          label="Needs Review"
          variant="outline"
          disabled={isSubmitting}
          onPress={() => handleSubmit('Pending')}
          style={styles.btn}
        />
      </View>

      <GlowButton
        label="Back"
        variant="outline"
        onPress={() => dispatch({ type: 'ADMIN_BACK' })}
        style={styles.backBtn}
      />
    </BackgroundGlow>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: vscale(6),
    paddingVertical: vscale(8),
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.lg,
    color: Colors.heading,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.body,
    textAlign: 'center',
  },
  inputWrapper: {
    width: '80%',
    maxWidth: scale(380),
  },
  textInput: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.heading,
    backgroundColor: Colors.white,
    borderWidth: 2,
    borderColor: Colors.primaryLight,
    borderRadius: Radius.md,
    padding: Spacing.xs,
    minHeight: vscale(70),
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  quickNotes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: vscale(4),
    maxWidth: scale(400),
  },
  quickNoteChip: {
    backgroundColor: Colors.bgTint,
    borderWidth: 1,
    borderColor: Colors.primaryLight,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.xs,
    paddingVertical: vscale(2),
  },
  quickNoteText: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.xs,
    color: Colors.primaryDark,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: vscale(4),
  },
  btn: {
    minWidth: scale(120),
  },
  backBtn: {
    minWidth: 120,
  },
});
