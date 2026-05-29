import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import LogoHeader from '../components/LogoHeader';
import PulsingRings from '../components/PulsingRings';
import HexGridPattern from '../components/HexGridPattern';
import FloatingLeaves from '../components/FloatingLeaves';
import { Colors, Fonts, FontSizes, Spacing, scale, vscale } from '../constants/theme';
import { useKiosk } from '../context/KioskContext';

export default function ThankYouScreen() {
  const { payload, dispatch } = useKiosk();

  const totalPoints = payload.totalPoints || 0;
  const totalBottles = payload.totalBottles || 0;

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const refCode = `ECO-${Date.now().toString(36).toUpperCase().slice(-6)}`;

  return (
    <TouchableOpacity
      style={{ flex: 1 }}
      activeOpacity={1}
      onPress={() => dispatch({ type: 'SYSTEM_CLEAR' })}
    >
      <LinearGradient
        colors={[Colors.bg, Colors.bgTint, '#DCFCE7']}
        style={styles.container}
      >
        {/* Background layers */}
        <HexGridPattern />
        <PulsingRings />
        <FloatingLeaves count={8} />
        <LogoHeader />

        {/* Thank You Heading */}
        <Text style={styles.heading}>Thank you for using EcoPoints!</Text>

        {/* Receipt Card */}
        <View style={styles.receiptCard}>
          {/* Top Perforation */}
          <View style={styles.perforation}>
            {Array.from({ length: 18 }).map((_, i) => (
              <View key={i} style={styles.perforationDot} />
            ))}
          </View>

          {/* Logo Section */}
          <View style={styles.logoSection}>
            <Image
              source={require('../../assets/favicon.png')}
              style={styles.receiptLogo}
              resizeMode="contain"
            />
            <Text style={styles.receiptBrand}>ECOPOINTS</Text>
            <Text style={styles.receiptSubtitle}>Official Transaction</Text>
          </View>

          {/* Dashed Divider */}
          <View style={styles.dashedDivider} />

          {/* Key-Value Rows */}
          <View style={styles.rowsSection}>
            <View style={styles.row}>
              <Text style={styles.rowLabel}>Description</Text>
              <Text style={styles.rowValue}>Bottle Recycling</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.rowLabel}>Date</Text>
              <Text style={styles.rowValueMono}>{dateStr}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.rowLabel}>Time</Text>
              <Text style={styles.rowValueMono}>{timeStr}</Text>
            </View>
            {totalBottles > 0 && (
              <View style={styles.row}>
                <Text style={styles.rowLabel}>Qty Recycled</Text>
                <Text style={styles.rowValueBold}>{totalBottles} Units</Text>
              </View>
            )}
            <View style={styles.row}>
              <Text style={styles.rowLabel}>Reference</Text>
              <Text style={styles.rowValueMono}>{refCode}</Text>
            </View>
          </View>

          {/* Dashed Divider */}
          <View style={styles.dashedDivider} />

          {/* Points Total Box */}
          <View style={styles.totalBox}>
            <Text style={styles.totalLabel}>POINTS TOTAL</Text>
            <Text style={styles.totalValue}>+{totalPoints}</Text>
          </View>

          {/* Thank You Message */}
          <View style={styles.messageSection}>
            <Text style={styles.thankYouMsg}>
              Thank you for helping us keep the campus green!
            </Text>
            <Text style={styles.verificationCode}>
              Verification Code: {refCode}
            </Text>
          </View>

          {/* Barcode Mockup */}
          <View style={styles.barcodeRow}>
            {Array.from({ length: 15 }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.barcodeLine,
                  { width: i % 4 === 0 ? 3 : 1.5 },
                ]}
              />
            ))}
          </View>

          {/* Bottom Jagged Edge */}
          <View style={styles.jaggedEdge}>
            {Array.from({ length: 20 }).map((_, i) => (
              <View key={i} style={styles.jaggedTriangle} />
            ))}
          </View>
        </View>

        {/* Anchor Hint text permanently to the bottom */}
        <Text style={styles.tapHint}>Tap anywhere to continue</Text>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const RECEIPT_WIDTH = scale(260);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.xs,
    overflow: 'hidden',
  },

  // Heading
  heading: {
    fontFamily: Fonts.headingBold,
    fontSize: FontSizes.xl * 1.2,
    color: Colors.heading,
    textAlign: 'center',
    zIndex: 10,
    marginTop: vscale(45), // Pushes the text block and the receipt downwards
  },
  subtitle: {
    fontFamily: Fonts.body,
    fontSize: FontSizes.md,
    color: Colors.primaryDark,
    textAlign: 'center',
    marginBottom: Spacing.xs,
    zIndex: 10,
  },

  // Receipt Card
  receiptCard: {
    width: RECEIPT_WIDTH,
    backgroundColor: Colors.white,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 30,
    elevation: 12,
    overflow: 'hidden',
    zIndex: 10,
  },

  // Top Perforation
  perforation: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 2,
  },
  perforationDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: '#A8A29E',
    opacity: 0.2,
    marginTop: -2,
  },

  // Logo Section
  logoSection: {
    alignItems: 'center',
    paddingTop: vscale(14),
    paddingBottom: vscale(8),
    paddingHorizontal: scale(16),
  },
  receiptLogo: {
    width: scale(60),
    height: scale(30),
    marginBottom: vscale(4),
  },
  receiptBrand: {
    fontFamily: Fonts.headingBold,
    fontSize: scale(16),
    color: '#292524',
    letterSpacing: -0.5,
  },
  receiptSubtitle: {
    fontFamily: Fonts.mono,
    fontSize: scale(7),
    color: '#A8A29E',
    textTransform: 'uppercase',
    letterSpacing: 3,
    marginTop: 2,
  },

  // Dashed Divider
  dashedDivider: {
    borderTopWidth: 1,
    borderStyle: 'dashed',
    borderTopColor: '#E7E5E4',
    marginHorizontal: scale(16),
    marginVertical: vscale(6),
  },

  // Key-Value Rows
  rowsSection: {
    paddingHorizontal: scale(16),
    gap: vscale(8),
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
  },
  rowLabel: {
    fontFamily: Fonts.mono,
    fontSize: scale(7),
    color: '#A8A29E',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  rowValue: {
    fontFamily: Fonts.bodyBold,
    fontSize: scale(9),
    color: '#44403C',
    textAlign: 'right',
    flexShrink: 1,
  },
  rowValueMono: {
    fontFamily: Fonts.mono,
    fontSize: scale(9),
    color: '#44403C',
  },
  rowValueBold: {
    fontFamily: Fonts.mono,
    fontSize: scale(9),
    color: '#44403C',
    fontWeight: '900',
  },

  // Points Total Box
  totalBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FAFAF9',
    marginHorizontal: scale(16),
    marginVertical: vscale(4),
    paddingHorizontal: scale(12),
    paddingVertical: vscale(8),
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#F5F5F4',
  },
  totalLabel: {
    fontFamily: Fonts.bodyBold,
    fontSize: scale(8),
    color: '#1C1917',
    textTransform: 'uppercase',
    letterSpacing: 2,
  },
  totalValue: {
    fontFamily: Fonts.headingBold,
    fontSize: scale(20),
    color: Colors.primary,
  },

  // Thank You Message
  messageSection: {
    alignItems: 'center',
    paddingHorizontal: scale(16),
    paddingTop: vscale(8),
    gap: vscale(3),
  },
  thankYouMsg: {
    fontFamily: Fonts.mono,
    fontSize: scale(7),
    color: '#A8A29E',
    textTransform: 'uppercase',
    textAlign: 'center',
    lineHeight: scale(12),
  },
  verificationCode: {
    fontFamily: Fonts.mono,
    fontSize: scale(6.5),
    color: Colors.primary,
    fontStyle: 'italic',
    fontWeight: 'bold',
  },

  // Barcode Mockup
  barcodeRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 2,
    paddingVertical: vscale(8),
    opacity: 0.35,
  },
  barcodeLine: {
    height: 18,
    backgroundColor: '#292524',
  },

  // Bottom Jagged Edge
  jaggedEdge: {
    flexDirection: 'row',
    height: 8,
  },
  jaggedTriangle: {
    flex: 1,
    height: 0,
    borderLeftWidth: RECEIPT_WIDTH / 40,
    borderRightWidth: RECEIPT_WIDTH / 40,
    borderTopWidth: 8,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: Colors.white,
    backgroundColor: 'transparent',
  },

  // Tap hint 
  tapHint: {
    position: 'absolute',
    bottom: vscale(20),
    alignSelf: 'center',
    fontFamily: Fonts.body,
    fontSize: FontSizes.sm,
    color: Colors.body,
    opacity: 0.6,
    zIndex: 10,
  },
});