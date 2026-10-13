import {
  OX2A, MRDNA_FRAME_BYTES_PER_BEAD, decodeMrdnaFrame,
} from '../formats/parsers/mrdna';

/**
 * Frames of an mrdna run, as the scene wants them.
 *
 * Frame 0 is the model itself — the bead mapping of the design, before the
 * engine minimised anything — and frame k is `.traj` frame k-1, or `.final`
 * when there is no `.traj`. Frames are bare doubles needing no parsing, so a
 * frame is read directly each time rather than cached.
 */

/**
 * A cube around frame 0, in oxDNA units. The model stores no box, and the beads
 * are not periodic, so this only has to hold the structure with room to move.
 */
export function mrdnaBox(pos, n) {
  let extent = 0;
  for (let axis = 0; axis < 3; axis++) {
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i < n; i++) {
      const v = pos[3 * i + axis];
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    extent = Math.max(extent, (hi - lo) / OX2A);
  }
  const side = extent * 1.5 + 4;
  return [side, side, side];
}

/**
 * Particles centred on the box by their centroid, as oxDNA frames are centred
 * on their centre of mass — which takes out drift — and never wrapped: wrapping
 * would cut every bond that crossed a wall.
 */
export function mrdnaParticles(pos, n, kind, box) {
  let cx = 0; let cy = 0; let cz = 0;
  for (let i = 0; i < n; i++) { cx += pos[3 * i]; cy += pos[3 * i + 1]; cz += pos[3 * i + 2]; }
  cx /= n; cy /= n; cz /= n;
  const out = new Array(n);
  for (let i = 0; i < n; i++) {
    out[i] = {
      x: (pos[3 * i] - cx) / OX2A + box[0] / 2,
      y: (pos[3 * i + 1] - cy) / OX2A + box[1] / 2,
      z: (pos[3 * i + 2] - cz) / OX2A + box[2] / 2,
      typeIndex: kind[i],
      particleType: null,
    };
  }
  return out;
}

const stem = (name) => name.replace(/\.[^.]*$/, '');

/** The file sharing the model's name stem, else the first, else null. */
export function pickCompanion(files, modelName) {
  if (!files?.length) return null;
  return files.find(f => stem(f.name) === stem(modelName)) ?? files[0];
}

export async function readMrdnaFrame(source, k) {
  if (k === 0) return source.modelPos;
  const bytes = source.n * MRDNA_FRAME_BYTES_PER_BEAD;
  const file = source.traj ?? source.final;
  const start = source.traj ? (k - 1) * bytes : 0;
  const buffer = await file.slice(start, start + bytes).arrayBuffer();
  return decodeMrdnaFrame(buffer, source.n);
}

/** The BD step a frame was written at: 0 for the model, else from `.energy`. */
export function frameTime(source, k) {
  if (k === 0) return 0;
  return source.energy[k - 1]?.step ?? k;
}

/** Total first, which is what the control bar's readout shows. */
export function frameEnergy(source, k) {
  const row = k > 0 ? source.energy[k - 1] : null;
  return row ? [row.total, row.bond, row.angle, row.dihedral, row.nonbonded] : [0];
}
