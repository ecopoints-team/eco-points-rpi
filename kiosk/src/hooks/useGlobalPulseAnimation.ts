import { useEffect, useRef } from 'react';
import { useSharedValue, withRepeat, withSequence, withTiming, Easing } from 'react-native-reanimated';

// Global reference to store start time for synchronization
let globalStartTime: number | null = null;

export function useGlobalPulseAnimation(duration: number, delay: number) {
  const scale_val = useSharedValue(1);
  const opacity = useSharedValue(1);
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Initialize global start time on first mount
    if (globalStartTime === null) {
      globalStartTime = Date.now();
    }

    // Only initialize animation once per component
    if (!hasInitialized.current) {
      hasInitialized.current = true;

      // Calculate delay based on global start time for synchronization
      const elapsedTime = Date.now() - globalStartTime;
      const adjustedDelay = Math.max(0, delay - (elapsedTime % (duration * 2)));

      setTimeout(() => {
        scale_val.value = withRepeat(
          withSequence(
            withTiming(1.3, { duration: duration / 2, easing: Easing.inOut(Easing.ease) }),
            withTiming(1, { duration: duration / 2, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          true
        );

        opacity.value = withRepeat(
          withSequence(
            withTiming(0.05, { duration: duration / 2, easing: Easing.inOut(Easing.ease) }),
            withTiming(0.15, { duration: duration / 2, easing: Easing.inOut(Easing.ease) })
          ),
          -1,
          true
        );
      }, adjustedDelay);
    }
  }, [duration, delay, scale_val, opacity]);

  return { scale: scale_val, opacity };
}

// Reset global timing (useful for testing or restart scenarios)
export function resetGlobalPulseAnimation() {
  globalStartTime = null;
}
