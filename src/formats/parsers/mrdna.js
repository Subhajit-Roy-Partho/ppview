/**
 * The bead model written by the mrdna Rust engine (`mrdna_rs run`).
 *
 * `X.model` is the engine's input: positions, nucleotides per bead and every
 * bonded term, in the layout of `rsbridge.export_model`. It carries no labels —
 * the engine only needs numbers — so what each bead and bond *is* is recovered
 * from the model's structure (see `classifyMrdna`). `X.traj` and `X.final` are
 * bare f64 frames, N×3 each; `X.energy` is one text row per `.traj` frame.
 *
 * Lengths are Å throughout; conversion to oxDNA units happens on load.
 */

export const OX2A = 8.518;
export const MRDNA_FRAME_BYTES_PER_BEAD = 24;

export const KIND = { DS: 0, SS: 1, OR: 2, UNKNOWN: 3 };
export const KIND_NAMES = ['ds', 'ss', 'or', 'bead'];
export const KIND_LABELS = ['Double-stranded', 'Single-stranded', 'Orientation', 'Bead'];

export const BOND = { HELIX: 0, CROSSOVER: 1, SS: 2, JUNCTION: 3, ORIENT: 4, UNKNOWN: 5 };
export const BOND_NAMES = ['helix', 'crossover', 'ss', 'junction', 'orient', 'bond'];
export const BOND_LABELS = ['Helix', 'Crossover', 'Single strand', 'Junction', 'Orientation', 'Bond'];

const MAGIC_LO = 0x444E4131;
const MAGIC_HI = 0x4D52;

export class MrdnaFormatError extends Error {
  constructor(message) {
    super(message);
    this.name = 'MrdnaFormatError';
  }
}

/** True when the first eight bytes are the `.model` magic number. */
export function hasMrdnaMagic(bytes) {
  if (!bytes || bytes.length < 8) return false;
  const view = new DataView(bytes.buffer, bytes.byteOffset, 8);
  return view.getUint32(0, true) === MAGIC_LO && view.getUint32(4, true) === MAGIC_HI;
}

/** A cursor that refuses to read past the end, so a truncated file says so. */
function reader(buffer) {
  const view = new DataView(buffer);
  let o = 0;
  const need = (bytes) => {
    if (o + bytes > buffer.byteLength) {
      throw new MrdnaFormatError('The mrdna model file ends early; it may be truncated.');
    }
  };
  const u64 = () => {
    need(8);
    const lo = view.getUint32(o, true);
    const hi = view.getUint32(o + 4, true);
    o += 8;
    if (hi >= 0x200000) throw new MrdnaFormatError('The mrdna model file holds an impossible count.');
    return hi * 2 ** 32 + lo;
  };
  return {
    u64,
    f64s(count) {
      need(8 * count);
      const out = new Float64Array(count);
      for (let i = 0; i < count; i++) out[i] = view.getFloat64(o + 8 * i, true);
      o += 8 * count;
      return out;
    },
    skip(bytes) { need(bytes); o += bytes; },
    get offset() { return o; },
  };
}

export function parseMrdnaModel(buffer) {
  if (!hasMrdnaMagic(new Uint8Array(buffer, 0, Math.min(8, buffer.byteLength)))) {
    throw new MrdnaFormatError('This is not an mrdna model file (its magic number is wrong).');
  }
  const r = reader(buffer);
  r.skip(8);
  const n = r.u64();
  const pos = r.f64s(3 * n);
  r.skip(8 * n);                        // diffusion constants
  const nts = r.f64s(n);
  r.skip(8 + 56 + 8);                   // kT, nonbonded parameters, nonbonded flag
  r.skip(8 * r.u64());                  // nonbonded atom list

  const index = (v) => {
    if (v >= n) throw new MrdnaFormatError(`The mrdna model names bead ${v}, but has only ${n} beads.`);
    return v;
  };

  const nBonds = r.u64();
  const bonds = new Int32Array(2 * nBonds);
  for (let b = 0; b < nBonds; b++) {
    bonds[2 * b] = index(r.u64());
    bonds[2 * b + 1] = index(r.u64());
    r.skip(16);                         // k, r0
  }
  r.skip(40 * r.u64());                 // angles: i j l k θ0
  const nDih = r.u64();
  const dihedrals = new Int32Array(4 * nDih);
  for (let d = 0; d < nDih; d++) {
    for (let k = 0; k < 4; k++) dihedrals[4 * d + k] = index(r.u64());
    r.skip(32);                         // k, φ0, rcm, rcq
  }
  r.skip(16 * r.u64());                 // exclusions

  if (r.offset !== buffer.byteLength) {
    throw new MrdnaFormatError(
      `The mrdna model has ${buffer.byteLength - r.offset} bytes after its last section.`);
  }
  return { n, pos, nts, bonds, dihedrals };
}

/**
 * What each bead and bond is, from the model's structure alone.
 *
 * - orientation beads are the only ones carrying no nucleotides;
 * - a double-stranded bead is one bonded to an orientation bead;
 * - every other bead is single-stranded;
 * - a ds–ds bond with a twist dihedral (orientation bead at both ends) across
 *   it lies along a helix; any other ds–ds bond is a crossover.
 *
 * Checked bead for bead and bond for bond against the Python BeadModel at 5, 3
 * and 1 bp/bead. A model built without local twist has no orientation beads,
 * and then nothing tells ds from ss — so nothing is guessed.
 */
export function classifyMrdna({ n, nts, bonds, dihedrals }) {
  const nBonds = bonds.length / 2;
  const kind = new Uint8Array(n);
  const bondType = new Uint8Array(nBonds);
  const parent = new Int32Array(n).fill(-1);

  let anyOrient = false;
  for (let i = 0; i < n; i++) if (nts[i] === 0) { anyOrient = true; break; }

  if (!anyOrient) {
    kind.fill(KIND.UNKNOWN);
    bondType.fill(BOND.UNKNOWN);
  } else {
    for (let i = 0; i < n; i++) kind[i] = nts[i] === 0 ? KIND.OR : KIND.SS;
    for (let b = 0; b < nBonds; b++) {
      const i = bonds[2 * b];
      const j = bonds[2 * b + 1];
      if (kind[i] === KIND.OR && kind[j] !== KIND.OR) { kind[j] = KIND.DS; parent[i] = j; }
      if (kind[j] === KIND.OR && kind[i] !== KIND.OR) { kind[i] = KIND.DS; parent[j] = i; }
    }
    const twisted = new Set();
    for (let d = 0; d < dihedrals.length / 4; d++) {
      const a = dihedrals[4 * d];
      const b = dihedrals[4 * d + 1];
      const c = dihedrals[4 * d + 2];
      const e = dihedrals[4 * d + 3];
      if (kind[a] === KIND.OR && kind[e] === KIND.OR) twisted.add(Math.min(b, c) * n + Math.max(b, c));
    }
    for (let b = 0; b < nBonds; b++) {
      const i = bonds[2 * b];
      const j = bonds[2 * b + 1];
      const ki = kind[i];
      const kj = kind[j];
      if (ki === KIND.OR || kj === KIND.OR) bondType[b] = BOND.ORIENT;
      else if (ki === KIND.DS && kj === KIND.DS) {
        bondType[b] = twisted.has(Math.min(i, j) * n + Math.max(i, j)) ? BOND.HELIX : BOND.CROSSOVER;
      } else if (ki === KIND.SS && kj === KIND.SS) bondType[b] = BOND.SS;
      else bondType[b] = BOND.JUNCTION;
    }
  }

  const counts = {
    beads: Object.fromEntries(KIND_NAMES.map(k => [k, 0])),
    bonds: Object.fromEntries(BOND_NAMES.map(b => [b, 0])),
  };
  kind.forEach(k => { counts.beads[KIND_NAMES[k]] += 1; });
  bondType.forEach(t => { counts.bonds[BOND_NAMES[t]] += 1; });
  return { kind, bondType, parent, counts };
}

export function mrdnaFrameCount(byteLength, n) {
  const frameBytes = n * MRDNA_FRAME_BYTES_PER_BEAD;
  return { frames: Math.floor(byteLength / frameBytes), remainder: byteLength % frameBytes };
}

export function decodeMrdnaFrame(buffer, n) {
  if (buffer.byteLength !== n * MRDNA_FRAME_BYTES_PER_BEAD) {
    throw new MrdnaFormatError(
      `An mrdna frame of ${n} beads is ${n * MRDNA_FRAME_BYTES_PER_BEAD} bytes; this one is ${buffer.byteLength}.`);
  }
  const view = new DataView(buffer);
  const out = new Float64Array(3 * n);
  for (let k = 0; k < 3 * n; k++) out[k] = view.getFloat64(8 * k, true);
  return out;
}

export function parseMrdnaEnergy(text) {
  const rows = [];
  for (const line of text.split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const [step, total, bond, angle, dihedral, nonbonded] = t.split(/\s+/).map(Number);
    rows.push({ step, total, bond, angle, dihedral, nonbonded });
  }
  return rows;
}

/** One line for the selection panel, or null when the scene is not mrdna. */
export function describeMrdnaBead(topData, index) {
  if (topData?.format !== 'mrdna') return null;
  const k = topData.kind[index];
  if (k === KIND.OR) return `orientation bead of ${topData.parent[index]}`;
  return `${KIND_NAMES[k]} bead · ${Number(topData.nts[index].toFixed(2))} nt`;
}
