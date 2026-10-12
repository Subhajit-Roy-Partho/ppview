import * as THREE from 'three';
import { beadRadius, orientMarker, beadVisible, MRDNA_COLORS } from './geometry';
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
});
