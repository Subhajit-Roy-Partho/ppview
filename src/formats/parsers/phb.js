/**
 * PHB (Patchy Helix Bundle) topology, as written for the oxDNA fork's `PHB`
 * interaction.
 *
 *   <totPar> <strands> <version> <patchySpacer>
 *   iP <id> <color> <strength> <x> <y> <z> <a1x a1y a1z> <a2x a2y a2z>
 *   iC <btype> <patchId1> <patchId2> ...        (btype -> list of iP ids)
 *   <type> <strand> <btype> <radius> <mass> [<neighbour> <k> <r0>]...
 *
 * Particle `type` -3 is the icosahedral core (radius ~1), -4 a helix-arm bead
 * (radius ~0.1). `btype` 100 means "no patches".
 *
 * Two things differ from the other patchy formats and are handled here rather
 * than in the renderers:
 *
 *  - Particles are typed by (type, btype), not by strand. A crystal has one
 *    strand per arm and one per core (thousands of them), but only a few dozen
 *    distinct patch layouts; one type per strand would mean one instanced layer
 *    per strand.
 *  - Patches are coloured by their interaction colour, not by their id. Two
 *    patches interact when `color_p + color_q == 0`, so a complementary pair
 *    must look identical (see `phbPatchPalette`).
 */

// Smallest radius, relative to the largest particle, that a bead is drawn at.
// The helix beads are 0.1 against a core of 1; drawn to scale they are sub-pixel
// dots in any scene large enough to be interesting.
export const PHB_MIN_RELATIVE_RADIUS = 0.25;

export const PHB_CORE_COLOR = '#c8ccd6';
export const PHB_ARM_COLOR = '#5f6f86';

/* ----------------------------- colour mapping ----------------------------- */

const hslToHex = (h, s, l) => {
  const a = s * Math.min(l, 1 - l);
  const f = (n) => {
    const k = (n + h / 30) % 12;
    const c = l - a * Math.max(-1, Math.min(k - 3, Math.min(9 - k, 1)));
    return Math.round(255 * c).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
};

const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));

/**
 * Colour for each PHB patch colour id.
 *
 * Complementary colours (c and -c) get exactly the same colour, so a matching
 * pair reads as one hue. Hue is keyed on `|c| mod 500`: the near-tip/core
 * patches (e.g. 21, -21) and the far-tip patches (e.g. 521, -521) of one arm
 * slot share a hue, and are told apart by tone (the 500s are the darker,
 * more saturated variant). Hues are spread by a golden-ratio stride over the
 * colours actually present, so neighbouring ids do not get neighbouring hues.
 *
 * The same rule is implemented in `render_phb.py`.
 *
 * @param {number[]} colors  raw `iP` colour ids (any sign)
 * @returns {{ colorOf: (c:number)=>string, legend: {key:number,label:string,hex:string}[] }}
 */
export function phbPatchPalette(colors) {
  const keys = [...new Set(colors.map(c => Math.abs(c) % 500))].sort((a, b) => a - b);
  const n = Math.max(keys.length, 1);
  let stride = Math.max(1, Math.round(n * 0.381966));
  while (gcd(stride, n) !== 1) stride += 1;
  const hueOf = new Map(keys.map((k, r) => [k, ((r * stride) % n) / n * 360]));

  const colorOf = (c) => {
    const abs = Math.abs(c);
    const hue = hueOf.get(abs % 500) ?? 0;
    return abs >= 500 ? hslToHex(hue, 0.85, 0.42) : hslToHex(hue, 0.8, 0.62);
  };

  const legend = [...new Set(colors.map(c => Math.abs(c)))]
    .sort((a, b) => a - b)
    .map(abs => ({ key: abs, label: `${abs} / -${abs}`, hex: colorOf(abs) }));

  return { colorOf, legend };
}

/* -------------------------------- parsing --------------------------------- */

export const parsePHBTopology = (content) => {
  const lines = content.split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0 && !l.startsWith('#'));

  const headerTokens = lines[0].split(/\s+/);
  const totalParticles = parseInt(headerTokens[0]);
  const numStrands = parseInt(headerTokens[1]);

  const patchDefs = new Map(); // patchId -> {id, color, strength, position, a1, a2}
  const colorDefs = new Map(); // btype   -> [patchId, ...]
  const particleList = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (line[0] === 'i') {
      const tokens = line.split(/\s+/);
      if (line[1] === 'P') {
        const id = parseInt(tokens[1]);
        patchDefs.set(id, {
          id,
          color: parseInt(tokens[2]),
          strength: parseFloat(tokens[3]),
          position: { x: parseFloat(tokens[4]), y: parseFloat(tokens[5]), z: parseFloat(tokens[6]) },
          a1: { x: parseFloat(tokens[7]), y: parseFloat(tokens[8]), z: parseFloat(tokens[9]) },
          a2: { x: parseFloat(tokens[10]), y: parseFloat(tokens[11]), z: parseFloat(tokens[12]) },
        });
      } else if (line[1] === 'C') {
        colorDefs.set(parseInt(tokens[1]),
          tokens.slice(2).map(t => parseInt(t)).filter(n => !isNaN(n)));
      }
      // iK, iM and other directive lines are skipped
      continue;
    }

    // Body: type strandId btype radius mass [neighborIdx k r0 ...]
    const tokens = line.split(/\s+/);
    if (tokens.length < 4) continue;

    const springConnections = [];
    for (let j = 5; j + 2 < tokens.length; j += 3) {
      springConnections.push({
        neighborIdx: parseInt(tokens[j]),
        k: parseFloat(tokens[j + 1]),
        r0: parseFloat(tokens[j + 2]),
      });
    }

    particleList.push({
      ptype: parseInt(tokens[0]),
      strandId: parseInt(tokens[1]),
      btype: parseInt(tokens[2]),
      radius: parseFloat(tokens[3]),
      mass: tokens.length > 4 ? parseFloat(tokens[4]) : 1.0,
      springConnections,
    });
  }

  // Deduplicate spring connections
  const seen = new Set();
  const globalSpringConnections = [];
  for (let i = 0; i < particleList.length; i++) {
    for (const { neighborIdx } of particleList[i].springConnections) {
      const key = `${Math.min(i, neighborIdx)}-${Math.max(i, neighborIdx)}`;
      if (!seen.has(key)) {
        seen.add(key);
        globalSpringConnections.push({ p1: i, p2: neighborIdx, springId: 0 });
      }
    }
  }

  // Colour mapping over every patch that is actually used by some particle.
  const palette = phbPatchPalette([...patchDefs.values()].map(p => p.color));
  const maxStrength = Math.max(1e-9, ...[...patchDefs.values()].map(p => Math.abs(p.strength)));
  const maxRadius = Math.max(1e-9, ...particleList.map(p => p.radius));

  const patchEntry = (id) => {
    const patch = patchDefs.get(id);
    if (!patch) return null;
    return {
      x: patch.position.x, y: patch.position.y, z: patch.position.z,
      patchId: id, color: patch.color, a1: patch.a1,
      strength: patch.strength,
    };
  };

  // One type per distinct (type, btype). Particle order is kept by the mapping.
  const typeOf = new Map();
  const particleTypes = [];
  const particleTypeMapping = particleList.map((p) => {
    const key = `${p.ptype}/${p.btype}`;
    let entry = typeOf.get(key);
    if (!entry) {
      const patchIds = p.btype === 100 ? [] : (colorDefs.get(p.btype) || []).filter(id => patchDefs.has(id));
      const patchPositions = patchIds.map(patchEntry);
      entry = {
        typeIndex: particleTypes.length,
        count: 0,
        patches: patchIds,
        patchPositions,
        // Colour by interaction colour; strength sets the cone size.
        patchColors: patchPositions.map(pp => palette.colorOf(pp.color)),
        patchScales: patchPositions.map(pp =>
          0.6 + 0.4 * Math.sqrt(Math.min(1, Math.abs(pp.strength) / maxStrength))),
        particleScale: Math.max(p.radius / maxRadius, PHB_MIN_RELATIVE_RADIUS),
        baseColor: p.ptype === -3 ? PHB_CORE_COLOR : PHB_ARM_COLOR,
        phbType: p.ptype,
      };
      typeOf.set(key, entry);
      particleTypes.push(entry);
    }
    entry.count += 1;
    return { typeIndex: entry.typeIndex, particleType: entry };
  });

  console.log(`PHB topology: ${totalParticles} particles, ${numStrands} strands, ` +
    `${patchDefs.size} patch defs, ${colorDefs.size} btypes, ${particleTypes.length} particle types, ` +
    `${globalSpringConnections.length} spring bonds`);

  return {
    totalParticles,
    typeCount: particleTypes.length,
    particleTypes,
    particleTypeMapping,
    springConnections: globalSpringConnections,
    // The largest particle (the core) sets the radius control; beads are
    // smaller by `particleScale`.
    srsParticleRadius: maxRadius,
    patchLegend: palette.legend,
    format: 'phb',
  };
};
