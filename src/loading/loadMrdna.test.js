import fs from 'fs';
import path from 'path';
import { loadSimulation } from './loadSimulation';
import { createLoadTokens, runLoad } from './staleness';
import { mrdnaBox, mrdnaParticles, pickCompanion, readMrdnaFrame } from './mrdnaFrames';
import { OX2A } from '../formats/parsers/mrdna';

const FIXTURES = path.join(__dirname, '..', 'formats', 'parsers', '__fixtures__', 'mrdna');
const bytesOf = (name) => {
  const b = fs.readFileSync(path.join(FIXTURES, name));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
const binaryFile = (name, buffer) => ({
  name,
  size: buffer.byteLength,
  arrayBuffer: async () => buffer,
  slice: (a, b) => ({ arrayBuffer: async () => buffer.slice(a, b) }),
});
const textFile = (name, text) => ({ name, size: text.length, text: async () => text });
const expected = JSON.parse(fs.readFileSync(path.join(FIXTURES, 'tetra_r5.expected.json'), 'utf8'));

const sceneOf = () => {
  const calls = {};
  const record = (key) => (value) => { calls[key] = value; };
  return {
    calls,
    setTopData: record('topData'),
    setPositions: record('positions'),
    setCurrentBoxSize: record('boxSize'),
    setCurrentTime: record('time'),
    setCurrentEnergy: record('energy'),
    setConfigIndex: record('configIndex'),
    setConfigTimes: record('configTimes'),
    setTotalConfigs: record('totalConfigs'),
    setTrajFile: record('trajFile'),
    setFormatParticleRadius: record('formatRadius'),
  };
};

const categorizedOf = (overrides) => ({
  mrdnaModels: [], mrdnaTrajectories: [], mrdnaFinals: [], mrdnaEnergies: [],
  clusterFiles: [], observableFiles: [], unknown: [], ...overrides,
});

const load = (categorized, scene = sceneOf()) => runLoad(() => loadSimulation({
  files: [], categorized, signal: createLoadTokens().begin(), scene,
})).then(outcome => ({ outcome, scene }));

const MODEL = binaryFile('tetra_r5.model', bytesOf('tetra_r5.model'));
const TRAJ = binaryFile('tetra_r5.traj', bytesOf('tetra_r5.traj'));
const ENERGY = textFile('tetra_r5.energy', fs.readFileSync(path.join(FIXTURES, 'tetra_r5.energy'), 'utf8'));

describe('loadMrdna', () => {
  it('loads the model as frame 0 and the trajectory after it', async () => {
    const { outcome, scene } = await load(categorizedOf({
      mrdnaModels: [MODEL], mrdnaTrajectories: [TRAJ], mrdnaEnergies: [ENERGY],
    }));
    expect(outcome.ok).toBe(true);
    const { topData, positions, totalConfigs, configIndex, trajFile, configTimes } = scene.calls;
    expect(topData.format).toBe('mrdna');
    expect(topData.count).toBe(expected.n);
    expect(topData.counts.beads).toEqual({ ds: 162, ss: 36, or: 162, bead: 0 });
    expect(positions).toHaveLength(expected.n);
    expect(totalConfigs).toBe(expected.frames + 1);
    expect(configIndex).toEqual(Array.from({ length: expected.frames + 1 }, (_, i) => i));
    expect(configTimes).toEqual([0, ...expected.energy_steps]);
    expect(trajFile.mrdna).toBe(true);
  });

  it('works with only the final frame', async () => {
    const final = binaryFile('tetra_r5.final', bytesOf('tetra_r5.final'));
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaFinals: [final] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(2);
  });

  it('shows the model alone when no frames came with it', async () => {
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(1);
  });

  it('keeps the whole frames of a trajectory cut short', async () => {
    const frame = expected.n * 24;
    const cut = binaryFile('tetra_r5.traj', bytesOf('tetra_r5.traj').slice(0, 3 * frame + 100));
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    const { outcome, scene } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaTrajectories: [cut] }));
    expect(outcome.ok).toBe(true);
    expect(scene.calls.totalConfigs).toBe(4);
    expect(warn).toHaveBeenCalledWith(expect.stringMatching(/100 bytes/));
    warn.mockRestore();
  });

  it('refuses a trajectory shorter than one frame of this model', async () => {
    const tiny = binaryFile('tetra_r5.traj', new ArrayBuffer(240));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaTrajectories: [tiny] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/360 beads/);
  });

  it('refuses a final frame of the wrong size', async () => {
    const wrong = binaryFile('tetra_r5.final', new ArrayBuffer(48));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [MODEL], mrdnaFinals: [wrong] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/final frame/);
  });

  it('asks for the model when only frames were dropped', async () => {
    const { outcome } = await load(categorizedOf({ mrdnaTrajectories: [TRAJ] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/\.model/);
  });

  it('turns a malformed model into a message', async () => {
    const broken = binaryFile('x.model', bytesOf('tetra_r5.model').slice(0, 300));
    const { outcome } = await load(categorizedOf({ mrdnaModels: [broken] }));
    expect(outcome.ok).toBe(false);
    expect(outcome.message).toMatch(/ends early/);
  });
});

describe('mrdnaFrames', () => {
  it('pairs a model with the trajectory sharing its name', () => {
    const files = [{ name: 'b.traj' }, { name: 'a.traj' }];
    expect(pickCompanion(files, 'a.model')).toBe(files[1]);
    expect(pickCompanion([{ name: 'other.traj' }], 'a.model')).toEqual({ name: 'other.traj' });
    expect(pickCompanion([], 'a.model')).toBeNull();
  });

  it('converts to oxDNA units and centres the beads in a box around them', () => {
    const pos = Float64Array.from([0, 0, 0, 2 * OX2A, 0, 0]);
    const box = mrdnaBox(pos, 2);
    expect(box[0]).toBeCloseTo(2 * 1.5 + 4);
    const particles = mrdnaParticles(pos, 2, Uint8Array.from([0, 1]), box);
    expect(particles[0].x).toBeCloseTo(box[0] / 2 - 1);
    expect(particles[1].x).toBeCloseTo(box[0] / 2 + 1);
    expect(particles[1].typeIndex).toBe(1);
  });

  it('reads frame k from the right slice of the trajectory', async () => {
    const source = { n: expected.n, modelPos: null, traj: TRAJ, final: null, frameCount: expected.frames + 1 };
    const last = await readMrdnaFrame(source, expected.frames);
    expect(Array.from(last.slice(0, 3))).toEqual(expected.last_frame_first_pos);
  });
});
