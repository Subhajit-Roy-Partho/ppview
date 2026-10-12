import { useUIStore } from './uiStore';

describe('mrdna display state', () => {
  it('starts with everything shown at natural size', () => {
    const { mrdnaDisplay, showMrdnaPanel } = useUIStore.getState();
    expect(showMrdnaPanel).toBe(true);
    expect(mrdnaDisplay.showOrient).toBe(true);
    expect(mrdnaDisplay.beadScale).toBe(1);
    expect(Object.values(mrdnaDisplay.bondTypes).every(Boolean)).toBe(true);
  });

  it('changes one bond type without touching the others, as a new object', () => {
    const before = useUIStore.getState().mrdnaDisplay;
    useUIStore.getState().setMrdnaBondType('orient', false);
    const after = useUIStore.getState().mrdnaDisplay;
    expect(after).not.toBe(before);
    expect(after.bondTypes.orient).toBe(false);
    expect(after.bondTypes.helix).toBe(true);
    useUIStore.getState().setMrdnaBondType('orient', true);
  });

  it('sets bead size and orientation beads', () => {
    useUIStore.getState().setMrdnaBeadScale(0.4);
    useUIStore.getState().setMrdnaShowOrient(false);
    expect(useUIStore.getState().mrdnaDisplay).toMatchObject({ beadScale: 0.4, showOrient: false });
    useUIStore.getState().setMrdnaBeadScale(1);
    useUIStore.getState().setMrdnaShowOrient(true);
  });
});
