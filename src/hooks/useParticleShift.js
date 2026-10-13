import { useCallback } from 'react';
import { useParticleStore } from '../store/particleStore';
import { applyPeriodicWrapping } from '../utils/geometryUtils';
import { isPeriodic } from '../formats/registry';

/**
 * Nudging every particle along one axis, for looking behind a dense structure.
 *
 * Wraps into the box for periodic formats only; a format with a synthetic box
 * (mrdna) is just translated, so beads never jump to the far wall. Never
 * re-centring: re-centring would move the structure back
 * under the camera and undo the shift the person just asked for.
 *
 * Reads positions through `getState()` because Zustand setters take a value, not
 * an updater, and subscribing here would rebuild this callback on every frame.
 */
export default function useParticleShift({ invalidateScene }) {
  const setPositions = useParticleStore(state => state.setPositions);
  const currentBoxSize = useParticleStore(state => state.currentBoxSize);

  return useCallback((axis, delta) => {
    const positions = useParticleStore.getState().positions;
    if (!Array.isArray(positions) || positions.length === 0) return;

    const shifted = positions.map(position => ({
      ...position,
      [axis]: position[axis] + delta,
    }));

    const { topData } = useParticleStore.getState();
    setPositions(isPeriodic(topData) ? applyPeriodicWrapping(shifted, currentBoxSize) : shifted);
    // frameloop is "demand", so a store write alone draws nothing.
    setTimeout(invalidateScene, 0);
  }, [currentBoxSize, invalidateScene, setPositions]);
}
