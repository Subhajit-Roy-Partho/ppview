import { detectFileType } from './detectFileType';
import { categorizeFiles } from './categorize';

// jsdom 16's Blob has neither text() nor arrayBuffer(), so files are faked with
// the two calls detection makes.
const fakeFile = (name, bytes) => ({
  name,
  size: bytes.length,
  slice: (start = 0, end = bytes.length) => {
    const part = bytes.slice(start, end);
    return {
      arrayBuffer: async () => part.buffer.slice(part.byteOffset, part.byteOffset + part.byteLength),
      text: async () => new TextDecoder().decode(part),
    };
  },
});
const textFile = (name, text) => fakeFile(name, new TextEncoder().encode(text));

const modelBytes = () => {
  const b = new Uint8Array(64);
  new DataView(b.buffer).setUint32(0, 0x444E4131, true);
  new DataView(b.buffer).setUint32(4, 0x4D52, true);
  new DataView(b.buffer).setUint32(8, 3, true);
  return b;
};
const frameBytes = () => new Uint8Array(Float64Array.from([1.5, -2.25, 3, 4, 5, 6, 7, 8, 9]).buffer);

describe('detectFileType for mrdna', () => {
  it('names each file of an mrdna run', async () => {
    expect(await detectFileType(fakeFile('a.model', modelBytes()))).toBe('mrdna-model');
    expect(await detectFileType(fakeFile('a.traj', frameBytes()))).toBe('mrdna-trajectory');
    expect(await detectFileType(fakeFile('a.final', frameBytes()))).toBe('mrdna-final');
    expect(await detectFileType(textFile('a.energy',
      '# step E_total E_bond E_angle E_dihedral E_nonbonded\n100 1 2 3 4 5\n'))).toBe('mrdna-energy');
  });

  it('leaves an oxDNA text trajectory named .traj to oxDNA', async () => {
    const text = ['t = 0', 'b = 10 10 10', 'E = 0 0 0', '1 2 3 1 0 0 0 0 1'].join('\n');
    expect(await detectFileType(textFile('trajectory.traj', text))).toBe('trajectory');
  });

  it('sorts an mrdna drop into its roles', () => {
    const m = { name: 'a.model' };
    const t = { name: 'a.traj' };
    const f = { name: 'a.final' };
    const e = { name: 'a.energy' };
    const c = categorizeFiles([
      { file: m, type: 'mrdna-model' }, { file: t, type: 'mrdna-trajectory' },
      { file: f, type: 'mrdna-final' }, { file: e, type: 'mrdna-energy' },
    ]);
    expect(c.mrdnaModels).toEqual([m]);
    expect(c.mrdnaTrajectories).toEqual([t]);
    expect(c.mrdnaFinals).toEqual([f]);
    expect(c.mrdnaEnergies).toEqual([e]);
    expect(c.trajectory).toBeNull();
    expect(c.unknown).toEqual([]);
  });
});
