import React from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { scale, vscale } from '../constants/theme';

interface LogoHeaderProps {
  logoSize?: number;
}

/**
 * Logo header component that displays the EcoPoints logo in the top-left corner.
 * Used on all screens except StartScreen.
 */
export default function LogoHeader({ logoSize = scale(110) }: LogoHeaderProps) {
  return (
    <View style={styles.container}>
      <Image
        source={require('../../assets/Logo EcoPoints.png')}
        style={[styles.logo, { width: logoSize, height: logoSize }]}
        resizeMode="contain"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: vscale(12),
    left: scale(30),
    zIndex: 100,
  },
  logo: {
    aspectRatio: 1,
  },
});
