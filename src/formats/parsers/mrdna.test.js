import fs from 'fs';
import path from 'path';
import {
  parseMrdnaModel, classifyMrdna, mrdnaFrameCount, decodeMrdnaFrame,
  parseMrdnaEnergy, describeMrdnaBead, MrdnaFormatError,
  KIND, KIND_NAMES, BOND, BOND_NAMES,
} from './mrdna';
import { encodeMrdnaModel } from './__fixtures__/encodeMrdnaModel';

const FIXTURES = path.join(__dirname, '__fixtures__', 'mrdna');
const bufferOf = (name) => {
  const b = fs.readFileSync(path.join(FIXTURES, name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
const expectedOf = (name) => JSON.parse(fs.readFileSync(path.join(FIXTURES, name), 'utf8'));

// Two helices of two ds beads each (with their orientation beads), joined by a
// crossover, and a two-bead single strand leaving the second helix.
//   0 ds  1 or(0)  2 ds  3 or(2)   helix A
//   4 ds  5 or(4)  6 ds  7 or(6)   helix B
//   8 ss  9 ss
const SYNTHETIC = {
  pos: Array.from({ length: 30 }, (_, i) => i),
  nts: [10, 0, 10, 0, 10, 0, 10, 0, 5, 5],
  bonds: [[0, 2], [0, 1], [2, 3], [4, 6], [4, 5], [6, 7], [2, 4], [6, 8], [8, 9]],
  dihedrals: [[1, 0, 2, 3], [5, 4, 6, 7], [0, 2, 4, 6]],
};

describe('parseMrdnaModel', () => {
  it.each(['tetra_r5', 'tetra_r1'])('reads %s as mrdna wrote it', (name) => {
    const expected = expectedOf(`${name}.expected.json`);
    const model = parseMrdnaModel(bufferOf(`${name}.model`));
    expect(model.n).toBe(expected.n);
    expect(model.bonds.length / 2).toBe(expected.bonds.length);
    expect(Array.from(model.pos.slice(0, 3))).toEqual(expected.first_pos);
    expected.bonds.forEach(([i, j], b) => {
      expect([model.bonds[2 * b], model.bonds[2 * b + 1]]).toEqual([i, j]);
    });
  });

  it('refuses a file that is not an mrdna model', () => {
    const buffer = encodeMrdnaModel(SYNTHETIC);
    new DataView(buffer).setUint32(0, 0, true);
    expect(() => parseMrdnaModel(buffer)).toThrow(MrdnaFormatError);
    expect(() => parseMrdnaModel(buffer)).toThrow(/not an mrdna model/);
  });

  it('refuses a truncated model rather than reading past its end', () => {
    const buffer = encodeMrdnaModel(SYNTHETIC).slice(0, 200);
    expect(() => parseMrdnaModel(buffer)).toThrow(/ends early/);
  });

  it('refuses a model with bytes left over', () => {
    const whole = new Uint8Array(encodeMrdnaModel(SYNTHETIC));
    const longer = new Uint8Array(whole.length + 8);
    longer.set(whole);
    expect(() => parseMrdnaModel(longer.buffer)).toThrow(/bytes after/);
  });

  it('refuses a bond to a bead that does not exist', () => {
    const buffer = encodeMrdnaModel({ ...SYNTHETIC, bonds: [[0, 99]] });
    expect(() => parseMrdnaModel(buffer)).toThrow(/bead 99/);
  });
});

describe('classifyMrdna', () => {
  it.each(['tetra_r5', 'tetra_r1'])('agrees with the Python model on every bead and bond of %s', (name) => {
    const expected = expectedOf(`${name}.expected.json`);
    const { kind, bondType, parent } = classifyMrdna(parseMrdnaModel(bufferOf(`${name}.model`)));
    expect(Array.from(kind, k => KIND_NAMES[k])).toEqual(expected.kind);
    expect(Array.from(parent)).toEqual(expected.parent);
    expect(Array.from(bondType, t => BOND_NAMES[t])).toEqual(expected.bonds.map(b => b[2]));
  });

  it('tells a crossover from a helix bond by the twist dihedral across it', () => {
    const { kind, bondType, parent, counts } = classifyMrdna(parseMrdnaModel(encodeMrdnaModel(SYNTHETIC)));
    expect(Array.from(kind, k => KIND_NAMES[k])).toEqual(
      ['ds', 'or', 'ds', 'or', 'ds', 'or', 'ds', 'or', 'ss', 'ss']);
    expect(Array.from(parent)).toEqual([-1, 0, -1, 2, -1, 4, -1, 6, -1, -1]);
    expect(Array.from(bondType, t => BOND_NAMES[t])).toEqual(
      ['helix', 'orient', 'orient', 'helix', 'orient', 'orient', 'crossover', 'junction', 'ss']);
    expect(counts.beads).toEqual({ ds: 4, ss: 2, or: 4, bead: 0 });
    expect(counts.bonds).toEqual({ helix: 2, crossover: 1, ss: 1, junction: 1, orient: 4, bond: 0 });
  });

  it('does not guess kinds for a model built without orientation beads', () => {
    const model = parseMrdnaModel(encodeMrdnaModel({
      pos: Array(9).fill(0), nts: [5, 5, 5], bonds: [[0, 1], [1, 2]],
    }));
    const { kind, bondType } = classifyMrdna(model);
    expect(Array.from(kind)).toEqual([KIND.UNKNOWN, KIND.UNKNOWN, KIND.UNKNOWN]);
    expect(Array.from(bondType)).toEqual([BOND.UNKNOWN, BOND.UNKNOWN]);
  });
});

describe('frames', () => {
  it('counts whole frames and reports a partial tail', () => {
    expect(mrdnaFrameCount(360 * 24 * 20, 360)).toEqual({ frames: 20, remainder: 0 });
    expect(mrdnaFrameCount(360 * 24 * 2 + 100, 360)).toEqual({ frames: 2, remainder: 100 });
    expect(mrdnaFrameCount(100, 360)).toEqual({ frames: 0, remainder: 100 });
  });

  it('decodes the last frame of the fixture trajectory', () => {
    const expected = expectedOf('tetra_r5.expected.json');
    const traj = bufferOf('tetra_r5.traj');
    const bytes = expected.n * 24;
    const last = decodeMrdnaFrame(traj.slice(traj.byteLength - bytes), expected.n);
    expect(Array.from(last.slice(0, 3))).toEqual(expected.last_frame_first_pos);
  });

  it('refuses a frame of the wrong size', () => {
    expect(() => decodeMrdnaFrame(new ArrayBuffer(48), 3)).toThrow(MrdnaFormatError);
  });
});

describe('parseMrdnaEnergy', () => {
  it('reads one row per trajectory frame', () => {
    const expected = expectedOf('tetra_r5.expected.json');
    const rows = parseMrdnaEnergy(fs.readFileSync(path.join(FIXTURES, 'tetra_r5.energy'), 'utf8'));
    expect(rows.map(r => r.step)).toEqual(expected.energy_steps);
    expect(Object.keys(rows[0])).toEqual(['step', 'total', 'bond', 'angle', 'dihedral', 'nonbonded']);
  });

  it('skips blank lines and the header', () => {
    expect(parseMrdnaEnergy('# step E_total E_bond E_angle E_dihedral E_nonbonded\n\n100 1 2 3 4 5\n'))
      .toEqual([{ step: 100, total: 1, bond: 2, angle: 3, dihedral: 4, nonbonded: 5 }]);
  });
});

describe('describeMrdnaBead', () => {
  const topData = { format: 'mrdna', kind: Uint8Array.from([0, 2, 1]), nts: Float64Array.from([10, 0, 2.5]), parent: Int32Array.from([-1, 0, -1]) };
  it('names the kind and the nucleotides a bead stands for', () => {
    expect(describeMrdnaBead(topData, 0)).toBe('ds bead · 10 nt');
    expect(describeMrdnaBead(topData, 1)).toBe('orientation bead of 0');
    expect(describeMrdnaBead(topData, 2)).toBe('ss bead · 2.5 nt');
  });
  it('says nothing for other formats', () => {
    expect(describeMrdnaBead({ format: 'lorenzo' }, 0)).toBeNull();
  });
});
