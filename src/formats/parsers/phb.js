// Function to parse PHB topology format
// Header: totPar strands version patchySpacer
// iP id color strength x y z a1x a1y a1z a2x a2y a2z
// iC colorId patchId1 patchId2 ...
// Body: type strandId btype radius mass [neighborIdx k r0 ...]
export const parsePHBTopology = (content) => {
  const lines = content.split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0 && !l.startsWith('#'));

  const headerTokens = lines[0].split(/\s+/);
  const totalParticles = parseInt(headerTokens[0]);
  const numStrands = parseInt(headerTokens[1]);

  const patchDefs = new Map(); // patchId → {id, color, strength, position, a1, a2}
  const colorDefs = new Map(); // colorId → [patchId, ...]
  const particleList = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (line[0] === 'i') {
      if (line[1] === 'P') {
        const tokens = line.split(/\s+/);
        const id = parseInt(tokens[1]);
        patchDefs.set(id, {
          id,
          color: parseInt(tokens[2]),
          strength: parseFloat(tokens[3]),
          position: { x: parseFloat(tokens[4]), y: parseFloat(tokens[5]), z: parseFloat(tokens[6]) },
          a1: { x: parseFloat(tokens[7]), y: parseFloat(tokens[8]), z: parseFloat(tokens[9]) },
          a2: { x: parseFloat(tokens[10]), y: parseFloat(tokens[11]), z: parseFloat(tokens[12]) }
        });
      } else if (line[1] === 'C') {
        const tokens = line.split(/\s+/);
        const colorId = parseInt(tokens[1]);
        const patchIds = tokens.slice(2).map(t => parseInt(t)).filter(n => !isNaN(n));
        colorDefs.set(colorId, patchIds);
      }
      // iK, iM and other directive lines are skipped
      continue;
    }

    // Body: type strandId btype radius mass [neighborIdx k r0 ...]
    const tokens = line.split(/\s+/);
    if (tokens.length < 4) continue;

    const strandId = parseInt(tokens[1]);
    const btype = parseInt(tokens[2]);
    const radius = parseFloat(tokens[3]);
    const mass = tokens.length > 4 ? parseFloat(tokens[4]) : 1.0;

    const springConnections = [];
    for (let j = 5; j + 2 < tokens.length; j += 3) {
      springConnections.push({
        neighborIdx: parseInt(tokens[j]),
        k: parseFloat(tokens[j + 1]),
        r0: parseFloat(tokens[j + 2])
      });
    }

    particleList.push({ strandId, btype, radius, mass, springConnections });
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

  // Map strand IDs → typeIndex (0, 1, 2, ...)
  const strandIds = [...new Set(particleList.map(p => p.strandId))].sort((a, b) => a - b);
  const strandToTypeIndex = new Map(strandIds.map((s, i) => [s, i]));

  // Per-particle patch lookup
  const getParticlePatchPositions = (btype) => {
    if (btype === 100) return { patchIds: [], patchPositions: [] };
    const patchIds = colorDefs.get(btype) || [];
    const patchPositions = patchIds.map(id => {
      const patch = patchDefs.get(id);
      if (!patch) return null;
      return { x: patch.position.x, y: patch.position.y, z: patch.position.z, patchId: id, color: patch.color, a1: patch.a1 };
    }).filter(Boolean);
    return { patchIds, patchPositions };
  };

  // Per-particle type mapping
  const particleTypeMapping = particleList.map(p => {
    const typeIndex = strandToTypeIndex.get(p.strandId) ?? 0;
    const { patchIds, patchPositions } = getParticlePatchPositions(p.btype);
    return {
      typeIndex,
      particleType: { typeIndex, count: 1, patches: patchIds, patchPositions }
    };
  });

  // Per-strand summary for legend/coloring
  const particleTypes = strandIds.map(strandId => {
    const typeIndex = strandToTypeIndex.get(strandId);
    const particlesOfStrand = particleList.filter(p => p.strandId === strandId);
    const allPatchIds = new Set();
    const allPatchPositions = [];
    for (const p of particlesOfStrand) {
      for (const id of (colorDefs.get(p.btype) || [])) {
        if (!allPatchIds.has(id)) {
          allPatchIds.add(id);
          const patch = patchDefs.get(id);
          if (patch) {
            allPatchPositions.push({ x: patch.position.x, y: patch.position.y, z: patch.position.z, patchId: id, color: patch.color, a1: patch.a1 });
          }
        }
      }
    }
    return { typeIndex, count: particlesOfStrand.length, patches: [...allPatchIds], patchPositions: allPatchPositions };
  });

  const representativeRadius = particleList.length > 0 ? particleList[0].radius : 0.5;

  console.log(`PHB topology: ${totalParticles} particles, ${numStrands} strands, ` +
    `${patchDefs.size} patch defs, ${colorDefs.size} color types, ${globalSpringConnections.length} spring bonds`);

  return {
    totalParticles,
    typeCount: strandIds.length,
    particleTypes,
    particleTypeMapping,
    springConnections: globalSpringConnections,
    srsParticleRadius: representativeRadius,
    format: 'phb'
  };
};
