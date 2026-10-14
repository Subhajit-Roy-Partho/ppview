import { KIND } from '../../formats/parsers/mrdna';

/** Kind colours: ds, ss, or, unknown. Bond colours: helix, crossover, ss, junction, orient, unknown. */
export const MRDNA_COLORS = {
  kind: ['#4a7fb5', '#e8903a', '#9aa0a6', '#b0b0b0'],
  bond: ['#2c4f7c', '#d64545', '#e8903a', '#8e5bb5', '#c8c8c8', '#888888'],
};

// A 5 bp double-stranded bead carries 10 nucleotides and is drawn about a helix
// radius across (1 nm ≈ 1.17 oxDNA units). Volume follows the nucleotides, so
// the radius goes as their cube root.
const REFERENCE_NTS = 10;
const REFERENCE_RADIUS = 1.0;
const OR_RADIUS = 0.25;
export const BOND_THICKNESS = 0.12;
export const ORIENT_THICKNESS = 0.05;

export function beadRadius(kind, nts) {
  if (kind === KIND.OR) return OR_RADIUS;
  return REFERENCE_RADIUS * Math.cbrt(Math.max(nts, 0.5) / REFERENCE_NTS);
}

/**
 * How far from its ds bead's centre an orientation marker is drawn: just outside
 * the surface, with one marker diameter of stalk between them. At the surface
 * itself the orient bond would lie wholly inside the ds sphere, where nothing
 * could show its colour, thickness or toggle.
 */
export function orientMarkerDistance(parentRadius, orRadius) {
  return parentRadius + 2 * orRadius;
}

/**
 * Where an orientation bead is drawn. It really sits 1.5 Å off the helix axis —
 * inside its ds bead, where nothing would show it — so it is drawn just outside
 * that bead's surface (`distance` from its centre, see orientMarkerDistance),
 * on a short stalk, in the direction it really points. That direction is the
 * information it carries: the local twist.
 */
export function orientMarker(target, parentCentre, orCentre, distance) {
  target.copy(orCentre).sub(parentCentre);
  const length = target.length();
  if (length < 1e-9) return target.copy(orCentre);
  return target.multiplyScalar(distance / length).add(parentCentre);
}

export function beadVisible(kind, appearance, display) {
  if (appearance?.hidden) return false;
  return kind !== KIND.OR || display.showOrient;
}

/**
 * Visibility of every bead. An orientation bead is drawn only while the ds bead
 * it belongs to is: otherwise it would float at a hidden bead's centre.
 */
export function beadVisibility(kind, parent, appearance, display) {
  const n = kind.length;
  const visible = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    if (kind[i] !== KIND.OR) visible[i] = beadVisible(kind[i], appearance[i], display) ? 1 : 0;
  }
  for (let i = 0; i < n; i++) {
    if (kind[i] !== KIND.OR) continue;
    const p = parent[i];
    visible[i] = beadVisible(kind[i], appearance[i], display) && (p < 0 || visible[p]) ? 1 : 0;
  }
  return visible;
}

/** A bond is drawn only if its type is switched on and both of its beads are. */
export function bondVisible(typeName, visibleI, visibleJ, display) {
  return !!display.bondTypes[typeName] && !!visibleI && !!visibleJ;
}

/** A bead that is not drawn cannot be clicked. */
export function pickableIndex(visible, instanceId) {
  return visible?.[instanceId] ? instanceId : null;
}
