import * as THREE from 'three';
import {
  beadRadius, orientMarker, orientMarkerDistance, beadVisible, beadVisibility, bondVisible,
  pickableIndex, MRDNA_COLORS,
} from './geometry';
import { KIND } from '../../formats/parsers/mrdna';

describe('mrdna bead geometry', () => {
  it('sizes a 5 bp double-stranded bead at about a helix radius', () => {
    expect(beadRadius(KIND.DS, 10)).toBeCloseTo(1.0);
    expect(beadRadius(KIND.DS, 2)).toBeCloseTo(Math.cbrt(0.2));
    expect(beadRadius(KIND.SS, 5)).toBeLessThan(beadRadius(KIND.DS, 10));
  });

  it('draws an orientation bead small, whatever it carries', () => {
    expect(beadRadius(KIND.OR, 0)).toBe(0.25);
  });

  it('puts the orientation marker on its ds bead surface, pointing the real way', () => {
    const parent = new THREE.Vector3(1, 1, 1);
    const real = new THREE.Vector3(1.18, 1, 1);    // 1.5 Å off the axis
    const marker = orientMarker(new THREE.Vector3(), parent, real, 0.9);
    expect(marker.x).toBeCloseTo(1.9);
    expect(marker.y).toBeCloseTo(1);
    expect(marker.z).toBeCloseTo(1);
  });

  it('hides orientation beads when they are switched off, and hidden beads always', () => {
    const shown = { hidden: false };
    expect(beadVisible(KIND.OR, shown, { showOrient: false })).toBe(false);
    expect(beadVisible(KIND.OR, shown, { showOrient: true })).toBe(true);
    expect(beadVisible(KIND.DS, { hidden: true }, { showOrient: true })).toBe(false);
  });

  it('has a colour for every kind and bond type', () => {
    expect(MRDNA_COLORS.kind).toHaveLength(4);
    expect(MRDNA_COLORS.bond).toHaveLength(6);
  });

  it('draws the orientation marker one marker diameter outside the parent surface', () => {
    const parent = new THREE.Vector3(1, 1, 1);
    const real = new THREE.Vector3(1, 1.18, 1);
    const distance = orientMarkerDistance(0.9, 0.25);
    expect(distance).toBeCloseTo(0.9 + 0.5);
    const marker = orientMarker(new THREE.Vector3(), parent, real, distance);
    expect(marker.distanceTo(parent)).toBeCloseTo(1.4);
    expect(marker.y - 1).toBeGreaterThan(0.9);
    expect(marker.x).toBeCloseTo(1);
  });

  it('hides an orientation bead whose ds parent is hidden', () => {
    const kind = Uint8Array.of(KIND.DS, KIND.OR, KIND.DS, KIND.OR);
    const parent = Int32Array.of(-1, 0, -1, 2);
    const appearance = [{ hidden: true }, { hidden: false }, { hidden: false }, { hidden: false }];
    const v = beadVisibility(kind, parent, appearance, { showOrient: true });
    expect(Array.from(v)).toEqual([0, 0, 1, 1]);
  });

  it('hides a bond whose type is off or whose bead is hidden', () => {
    const on = { showOrient: false, bondTypes: { helix: true, orient: true } };
    // a hidden or bead (showOrient false) takes its orient bond with it
    expect(bondVisible('orient', 1, 0, on)).toBe(false);
    expect(bondVisible('helix', 1, 1, on)).toBe(true);
    expect(bondVisible('helix', 1, 1, { bondTypes: { helix: false } })).toBe(false);
  });

  it('lets a click select only a drawn bead', () => {
    const visible = Uint8Array.of(1, 0);
    expect(pickableIndex(visible, 0)).toBe(0);
    expect(pickableIndex(visible, 1)).toBeNull();
    expect(pickableIndex(undefined, 0)).toBeNull();
  });
});
