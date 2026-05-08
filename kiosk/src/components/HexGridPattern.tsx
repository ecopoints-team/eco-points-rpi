import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Path, Circle, Line, G } from 'react-native-svg';
import { Colors, scale } from '../constants/theme';

interface HexGridPatternProps {
  variant?: 'light' | 'dark';
}

// Generate hexagon path at given center
function hexPath(cx: number, cy: number, r: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    const x = cx + r * Math.cos(angle);
    const y = cy + r * Math.sin(angle);
    pts.push(`${x},${y}`);
  }
  return `M ${pts.join(' L ')} Z`;
}

// Pre-compute hex grid positions
const HEX_RADIUS = 28;
const HEX_H = HEX_RADIUS * 2;
const HEX_W = Math.sqrt(3) * HEX_RADIUS;
const COLS = Math.ceil(1200 / HEX_W) + 1;
const ROWS = Math.ceil(720 / (HEX_H * 0.75)) + 1;

interface HexNode {
  cx: number;
  cy: number;
  bright: boolean;
}

const hexNodes: HexNode[] = [];
// Use a seed-like approach for deterministic "random" highlights
for (let row = 0; row < ROWS; row++) {
  for (let col = 0; col < COLS; col++) {
    const cx = col * HEX_W + (row % 2 === 1 ? HEX_W / 2 : 0);
    const cy = row * HEX_H * 0.75;
    // Deterministic pseudo-random: highlight ~8% of hexagons
    const hash = (row * 37 + col * 13 + 7) % 100;
    hexNodes.push({ cx, cy, bright: hash < 8 });
  }
}

// Pre-compute circuit lines (connect some bright nodes to neighbors)
interface CircuitLine {
  x1: number; y1: number; x2: number; y2: number;
}

const circuitLines: CircuitLine[] = [];
const brightNodes = hexNodes.filter(n => n.bright);
brightNodes.forEach((node, i) => {
  // Connect to next bright node if close enough
  const next = brightNodes[(i + 1) % brightNodes.length];
  const dist = Math.sqrt((node.cx - next.cx) ** 2 + (node.cy - next.cy) ** 2);
  if (dist < HEX_W * 4 && dist > 0) {
    circuitLines.push({ x1: node.cx, y1: node.cy, x2: next.cx, y2: next.cy });
  }
});

export default function HexGridPattern({ variant = 'light' }: HexGridPatternProps) {
  const color = variant === 'dark' ? Colors.primaryLight : Colors.primary;
  const baseOpacity = variant === 'dark' ? 0.06 : 0.04;
  const brightOpacity = variant === 'dark' ? 0.14 : 0.1;
  const lineOpacity = variant === 'dark' ? 0.08 : 0.05;

  return (
    <View style={styles.container} pointerEvents="none">
      <Svg
        width="100%"
        height="100%"
        viewBox="0 0 1200 720"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Hex grid */}
        {hexNodes.map((node, i) => (
          <Path
            key={`hex-${i}`}
            d={hexPath(node.cx, node.cy, HEX_RADIUS)}
            fill="none"
            stroke={color}
            strokeWidth={0.6}
            opacity={node.bright ? brightOpacity : baseOpacity}
          />
        ))}

        {/* Bright node center dots */}
        {brightNodes.map((node, i) => (
          <Circle
            key={`dot-${i}`}
            cx={node.cx}
            cy={node.cy}
            r={2.5}
            fill={color}
            opacity={brightOpacity * 0.8}
          />
        ))}

        {/* Circuit connector lines */}
        {circuitLines.map((line, i) => (
          <Line
            key={`cline-${i}`}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke={color}
            strokeWidth={0.8}
            opacity={lineOpacity}
            strokeDasharray="4,6"
          />
        ))}
      </Svg>
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
