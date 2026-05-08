import { Dimensions } from 'react-native';

const { width, height } = Dimensions.get('window');

export const scale = (n: number) => (n / 1024) * width;
export const vscale = (n: number) => (n / 600) * height;

export const Colors = {
  primary: '#10B981',
  primaryLight: '#34D399',
  primaryDark: '#059669',
  heading: '#064E3B',
  hover: '#065F46',
  body: '#6B7280',
  bgTint: '#F0FDF4',
  bg: '#F8FAFC',
  accent: '#FBBF24',
  white: '#FFFFFF',
  error: '#EF4444',
  errorLight: '#FEE2E2',
  accentLight: '#FEF3C7',
  overlay: 'rgba(6, 78, 59, 0.7)',
};

export const Fonts = {
  heading: 'Fredoka_400Regular',
  headingBold: 'Fredoka_600SemiBold',
  body: 'Quicksand_500Medium',
  bodyBold: 'Quicksand_700Bold',
  mono: 'SpaceMono_400Regular',
};

export const Spacing = {
  xs: scale(8),
  sm: scale(16),
  md: scale(24),
  lg: scale(40),
  xl: scale(64),
};

export const FontSizes = {
  xs: scale(15),
  sm: scale(18),
  md: scale(22),
  lg: scale(32),
  xl: scale(40),
  xxl: scale(56),
  hero: scale(80),
};

export const Radius = {
  sm: 8,
  md: 16,
  lg: 24,
  full: 9999,
};
