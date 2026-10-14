import { parsePHBTopology, phbPatchPalette, PHB_MIN_RELATIVE_RADIUS } from './phb';
import { parsePSP2Topology } from './psp2';
import { analyzeTopologyFile } from '../detection/signatures';

const PHB = `5 3 1 0.1
iP 0 21 100 0 1 0 1 0 0 1 0 0
iP 1 522 100 1 0 0 1 0 0 1 0 0
iP 2 -21 100 -0.1 0 0 1 0 0 1 0 0
iP 3 -522 1 0.1 0 0 1 0 0 1 0 0
iC 0 0 1
iC 1 2
iC 2 3
-4 0 1 0.1 1 1 100 0.2
-4 0 100 0.1 1 0 100 0.2
-4 0 2 0.1 1
-3 1 0 1 10
-3 2 0 1 10
`;

describe('PHB topology', () => {
  const top = parsePHBTopology(PHB);

  it('is detected as phb, not srs springs', () => {
    expect(analyzeTopologyFile(PHB.split('\n'))).toBe('topology-phb');
  });

  it('types particles by (type, btype) rather than by strand', () => {
    expect(top.particleTypeMapping).toHaveLength(5);
    // the two cores share a type even though they are different strands
    expect(top.particleTypeMapping[3].typeIndex).toBe(top.particleTypeMapping[4].typeIndex);
    expect(top.typeCount).toBe(4);
  });

  it('draws small beads at a visible minimum size relative to the core', () => {
    const [bead, , , core] = top.particleTypeMapping.map(m => m.particleType);
    expect(core.particleScale).toBe(1);
    expect(bead.particleScale).toBeCloseTo(PHB_MIN_RELATIVE_RADIUS);
    expect(top.srsParticleRadius).toBe(1);
  });

  it('gives complementary patch colours the same display colour', () => {
    const core = top.particleTypeMapping[3].particleType;
    const bead = top.particleTypeMapping[0].particleType;   // btype 1 -> patch 2 (-21)
    expect(core.patchColors[0]).toBe(bead.patchColors[0]);  // 21 and -21
    const arm = top.particleTypeMapping[2].particleType;    // btype 2 -> patch 3 (-522)
    expect(arm.patchColors[0]).not.toBe(bead.patchColors[0]);
  });

  it('keeps spring bonds and a legend with one entry per |colour|', () => {
    expect(top.springConnections.length).toBeGreaterThan(0);
    expect(top.patchLegend.map(e => e.key)).toEqual([21, 522]);
  });
});

describe('phbPatchPalette', () => {
  it('maps c and -c identically and 21 / 521 to the same hue family but different tones', () => {
    const { colorOf } = phbPatchPalette([21, -21, 521, -521, 22, -22]);
    expect(colorOf(21)).toBe(colorOf(-21));
    expect(colorOf(521)).toBe(colorOf(-521));
    expect(colorOf(21)).not.toBe(colorOf(521));
    expect(colorOf(21)).not.toBe(colorOf(22));
  });
});

describe('PSP2 topology', () => {
  const PSP2 = `2 1 1 1
# PSP2 test
iP 0 1 100 0 0 1
iS 0 100 0.1 0 0 1
0 0 5 1 1 0 1 0
0 0 5 1 1 0 0 0
`;
  it('is detected from its comment and tagged psp2', () => {
    expect(analyzeTopologyFile(PSP2.split('\n'))).toBe('topology-psp2');
    expect(parsePSP2Topology(PSP2).format).toBe('psp2');
  });
});
