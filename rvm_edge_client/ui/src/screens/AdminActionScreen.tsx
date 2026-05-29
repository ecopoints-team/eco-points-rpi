import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BackgroundGlow from '../components/BackgroundGlow';
import LogoHeader from '../components/LogoHeader';
import GlowButton from '../components/GlowButton';
import StatusBadge from '../components/StatusBadge';
import { useKiosk } from '../context/KioskContext';
import { Colors, Fonts, FontSizes, Spacing, scale } from '../constants/theme';

const CATEGORY_DATA: Record<string, { title: string; actions: string[] }> = {
  maintenance: {
    title: 'Maintenance',
    actions: ['Cable Maintenance', 'Sensor Error', 'Camera Error', 'Connection Error', 'Motor Failure'],
  },
  diagnostics: {
    title: 'Diagnostics',
    actions: ['Machine Checkup', 'Software Update'],
  },
  clearing: {
    title: 'Clearing',
    actions: ['Bin Full'],
  },
};

export default function AdminActionScreen() {
  const { payload, dispatch } = useKiosk();
  const category = payload.adminCategory ?? 'maintenance';
  const data = CATEGORY_DATA[category] ?? CATEGORY_DATA.maintenance;

  return (
    <BackgroundGlow style={styles.container}>
      <LogoHeader />
      <StatusBadge label="ADMIN MODE" variant="warning" />

      <Text style={styles.title}>{data.title}</Text>
      <Text style={styles.subtitle}>Select the specific concern</Text>

      <View style={styles.actionList}>
        {data.actions.map((action) => (
          <GlowButton
            key={action}
            label={action}
            onPress={() =>
              dispatch({ type: 'ADMIN_SELECT_ACTION', payload: { action } })
            }
            style={styles.actionBtn}
          />
        ))}
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
    gap: Spacing.sm,
  },
  title: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xl,
    color: Colors.heading,
    textAlign: 'center',
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.body,
    textAlign: 'center',
  },
  actionList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: Spacing.xs,
    marginTop: Spacing.xs,
    width: '90%',
    maxWidth: scale(500),
  },
  actionBtn: {
    minWidth: scale(180),
    flexGrow: 0,
  },
  backBtn: {
    minWidth: 140,
    marginTop: Spacing.sm,
  },
});
