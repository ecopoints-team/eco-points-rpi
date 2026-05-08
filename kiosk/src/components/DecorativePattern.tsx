import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import Svg, { Circle, Line, Polyline } from 'react-native-svg';
import { Colors, scale, vscale } from '../constants/theme';

interface DecorativePatternProps {
  style?: ViewStyle;
  type?: 'dots' | 'waves' | 'grid';
  variant?: 'light' | 'dark';
}

export default function DecorativePattern({ 
  style, 
  type = 'dots', 
  variant = 'light' 
}: DecorativePatternProps) {
  
  const patternColor = variant === 'dark' ? Colors.primaryLight : Colors.primary;
  const patternOpacity = variant === 'dark' ? 0.08 : 0.05;

  // Calculate grid dimensions based on common screen sizes
  const dotSpacing = scale(24);
  const dotsPerRow = Math.ceil(1200 / dotSpacing);
  const dotsPerCol = Math.ceil(720 / dotSpacing);
  const dotRadius = scale(1.5);

  const wavePeriod = scale(60);
  const waveAmplitude = scale(8);
  const strokeWidth = scale(0.8);

  return (
    <View style={[styles.container, style]}>
      {type === 'dots' && (
        <Svg width="100%" height="100%" viewBox={`0 0 1200 720`} preserveAspectRatio="xMidYMid slice">
          {/* Dotted grid pattern */}
          {Array.from({ length: dotsPerRow }).map((_, x) =>
            Array.from({ length: dotsPerCol }).map((_, y) => (
              <Circle
                key={`dot-${x}-${y}`}
                cx={x * dotSpacing + dotSpacing / 2}
                cy={y * dotSpacing + dotSpacing / 2}
                r={dotRadius}
                fill={patternColor}
                opacity={patternOpacity}
              />
            ))
          )}
        </Svg>
      )}

      {type === 'waves' && (
        <Svg width="100%" height="100%" viewBox={`0 0 1200 720`} preserveAspectRatio="xMidYMid slice">
          {/* Wave pattern */}
          {Array.from({ length: 8 }).map((_, i) => {
            const yOffset = (i * 90) + 60;
            const points = Array.from({ length: 50 }).map((_, x) => {
              const xPos = (x * 24) + 60;
              const yPos = yOffset + Math.sin((x * Math.PI) / 6) * waveAmplitude;
              return `${xPos},${yPos}`;
            }).join(' ');

            return (
              <Polyline
                key={`wave-${i}`}
                points={points}
                fill="none"
                stroke={patternColor}
                strokeWidth={strokeWidth}
                opacity={patternOpacity}
              />
            );
          })}
        </Svg>
      )}

      {type === 'grid' && (
        <Svg width="100%" height="100%" viewBox={`0 0 1200 720`} preserveAspectRatio="xMidYMid slice">
          {/* Grid pattern */}
          {Array.from({ length: dotsPerRow }).map((_, x) => (
            <Line
              key={`vline-${x}`}
              x1={x * dotSpacing + dotSpacing / 2}
              y1="0"
              x2={x * dotSpacing + dotSpacing / 2}
              y2="720"
              stroke={patternColor}
              strokeWidth={strokeWidth}
              opacity={patternOpacity * 0.6}
            />
          ))}
          {Array.from({ length: dotsPerCol }).map((_, y) => (
            <Line
              key={`hline-${y}`}
              x1="0"
              y1={y * dotSpacing + dotSpacing / 2}
              x2="1200"
              y2={y * dotSpacing + dotSpacing / 2}
              stroke={patternColor}
              strokeWidth={strokeWidth}
              opacity={patternOpacity * 0.6}
            />
          ))}
        </Svg>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 0,
  },
});
