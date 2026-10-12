/**
 * Writes a `.model` buffer in the layout of mrdna's rsbridge.export_model, for
 * tests that need a model the real fixtures do not contain — crossovers, which
 * the tetrahelix has none of, and the malformed files the parser must refuse.
 */
export function encodeMrdnaModel({
  pos, nts, bonds = [], angles = [], dihedrals = [], excl = [], nbAtoms = [],
}) {
  const n = nts.length;
  const size = 16 + 24 * n + 8 * n + 8 * n + 8 + 56 + 8
    + 8 + 8 * nbAtoms.length
    + 8 + 32 * bonds.length
    + 8 + 40 * angles.length
    + 8 + 64 * dihedrals.length
    + 8 + 16 * excl.length;
  const buffer = new ArrayBuffer(size);
  const view = new DataView(buffer);
  let o = 0;
  const u64 = (v) => {
    view.setUint32(o, v % 2 ** 32, true);
    view.setUint32(o + 4, Math.floor(v / 2 ** 32), true);
    o += 8;
  };
  const f64 = (v) => { view.setFloat64(o, v, true); o += 8; };

  u64(0x4D52444E4131);
  u64(n);
  pos.forEach(f64);
  for (let i = 0; i < n; i++) f64(1);          // diffusion constants
  nts.forEach(f64);
  f64(0.586);                                  // kT
  for (let k = 0; k < 7; k++) f64(0);          // nonbonded parameters
  u64(1);                                      // nonbonded flag
  u64(nbAtoms.length); nbAtoms.forEach(u64);
  u64(bonds.length);
  bonds.forEach(([i, j]) => { u64(i); u64(j); f64(1); f64(1); });
  u64(angles.length);
  angles.forEach(([i, j, l]) => { u64(i); u64(j); u64(l); f64(1); f64(Math.PI); });
  u64(dihedrals.length);
  dihedrals.forEach(([i, j, k, l]) => { u64(i); u64(j); u64(k); u64(l); f64(1); f64(0); f64(0); f64(0); });
  u64(excl.length);
  excl.forEach(([a, b]) => { u64(a); u64(b); });
  return buffer;
}
