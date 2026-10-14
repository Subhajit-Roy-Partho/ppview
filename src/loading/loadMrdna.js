import {
  parseMrdnaModel, classifyMrdna, parseMrdnaEnergy, mrdnaFrameCount,
  MrdnaFormatError, MRDNA_FRAME_BYTES_PER_BEAD,
} from '../formats/parsers/mrdna';
import {
  mrdnaBox, mrdnaParticles, pickCompanion, frameTime,
} from './mrdnaFrames';
import { step, LoadError } from './staleness';

/**
 * An mrdna run: a `.model`, and optionally its `.traj` or `.final` and its
 * `.energy`. Self-contained like MGL — no topology or oxDNA trajectory is
 * involved — so it sets the whole scene up here.
 */
export async function loadMrdna(categorized, signal, scene, status) {
  const modelFile = categorized.mrdnaModels[0];
  if (!modelFile) {
    throw new LoadError(
      'These are mrdna frames, but the run’s .model file was not dropped with them. Drop the .model too.');
  }

  status('Reading the mrdna model');
  let model;
  try {
    model = parseMrdnaModel(await step(signal, modelFile.arrayBuffer()));
  } catch (error) {
    if (error instanceof MrdnaFormatError) throw new LoadError(error.message);
    throw error;
  }
  const { n } = model;
  const classes = classifyMrdna(model);

  const traj = pickCompanion(categorized.mrdnaTrajectories, modelFile.name);
  const final = traj ? null : pickCompanion(categorized.mrdnaFinals, modelFile.name);
  const energyFile = pickCompanion(categorized.mrdnaEnergies, modelFile.name);
  const frameBytes = n * MRDNA_FRAME_BYTES_PER_BEAD;

  let recorded = 0;
  if (traj) {
    const { frames, remainder } = mrdnaFrameCount(traj.size, n);
    if (frames === 0) {
      throw new LoadError(
        `${traj.name} is shorter than one frame of this model (${n} beads, ${frameBytes} bytes a frame). `
        + 'It may belong to a different run.');
    }
    if (remainder) {
      console.warn(`${traj.name}: ignoring ${remainder} bytes after the last whole frame.`);
    }
    recorded = frames;
  } else if (final) {
    if (final.size !== frameBytes) {
      throw new LoadError(
        `${final.name} is not one final frame of this model (${n} beads, ${frameBytes} bytes).`);
    }
    recorded = 1;
  }

  let energy = [];
  if (energyFile) {
    energy = parseMrdnaEnergy(await step(signal, energyFile.text()));
    if (traj && energy.length !== recorded) {
      console.warn(`${energyFile.name} has ${energy.length} rows for ${recorded} frames; using what matches.`);
    }
    if (!traj) energy = [];       // a .final has no row of its own
  }

  const box = mrdnaBox(model.pos, n);
  const source = {
    mrdna: true,
    name: modelFile.name,
    n,
    kind: classes.kind,
    modelPos: model.pos,
    traj,
    final,
    frameCount: recorded + 1,
    energy,
    box,
  };

  scene.setTopData({
    format: 'mrdna',
    count: n,
    nts: model.nts,
    bonds: model.bonds,
    ...classes,
  });
  scene.setPositions(mrdnaParticles(model.pos, n, classes.kind, box));
  scene.setCurrentBoxSize(box);
  scene.setCurrentTime(0);
  scene.setCurrentEnergy([0]);
  const frames = Array.from({ length: source.frameCount }, (_, k) => k);
  scene.setTrajFile(source);
  scene.setConfigIndex(frames);
  scene.setConfigTimes(frames.map(k => frameTime(source, k)));
  scene.setTotalConfigs(source.frameCount);
}
