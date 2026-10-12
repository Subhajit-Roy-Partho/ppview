import React, { useCallback, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';
import InstancedLayer from '../../rendering/InstancedLayer';
import { useRegisterPickable } from '../../rendering/pickingService';
import { centreOnBox, cylinderScratch, cylinderBetweenPoints } from '../../rendering/transforms';
import useClusterVisuals from '../../rendering/useClusterVisuals';
import { KIND, BOND, BOND_NAMES } from '../../formats/parsers/mrdna';
import {
  MRDNA_COLORS, beadRadius, orientMarker, beadVisible, BOND_THICKNESS, ORIENT_THICKNESS,
} from './geometry';

/**
 * The mrdna bead model: one sphere per bead, one cylinder per bond.
 *
 * Bead colour and scale go through the shared cluster appearance, so selection
 * and clustering apply here as everywhere else. A bond is drawn only while both
 * of its beads are.
 */
function MrdnaBeads() {
  const positions = useParticleStore(state => state.positions);
  const boxSize = useParticleStore(state => state.currentBoxSize);
  const topData = useParticleStore(state => state.topData);
  const particleRadius = useParticleStore(state => state.particleRadius);
  const baseParticleRadius = useParticleStore(state => state.baseParticleRadius);
  const sphereSegments = useUIStore(state => state.sphereSegments);
  const display = useUIStore(state => state.mrdnaDisplay);
  const appearanceOf = useClusterVisuals();
  const beadMeshRef = useRef();

  const n = topData?.count ?? 0;
  const ready = topData?.format === 'mrdna' && n > 0 && positions.length === n;
  const bondCount = ready ? topData.bondType.length : 0;
  const radiusScale = particleRadius / (baseParticleRadius || 1);

  const kindColors = useMemo(() => MRDNA_COLORS.kind.map(c => new THREE.Color(c)), []);
  const bondColors = useMemo(() => MRDNA_COLORS.bond.map(c => new THREE.Color(c)), []);
  const beadGeometry = useMemo(
    () => new THREE.SphereGeometry(1, sphereSegments, sphereSegments), [sphereSegments]);
  const bondGeometry = useMemo(
    () => new THREE.CylinderGeometry(1, 1, 1, Math.max(6, Math.round(sphereSegments / 2))), [sphereSegments]);
  const material = useMemo(() => new THREE.MeshStandardMaterial({ metalness: 0.1, roughness: 0.7 }), []);
  const bondMaterial = useMemo(() => new THREE.MeshStandardMaterial({ metalness: 0.1, roughness: 0.6 }), []);

  const appearance = useMemo(() => {
    if (!ready) return [];
    return Array.from({ length: n }, (_, i) => appearanceOf(i, { baseColor: kindColors[topData.kind[i]] }));
  }, [ready, n, topData, appearanceOf, kindColors]);

  // Where each bead is drawn and how big, once per frame or display change.
  const layout = useMemo(() => {
    if (!ready) return null;
    const { kind, nts, parent } = topData;
    const centres = Array.from({ length: n }, (_, i) => centreOnBox(new THREE.Vector3(), positions[i], boxSize));
    const radii = new Float32Array(n);
    const visible = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      radii[i] = beadRadius(kind[i], nts[i]) * display.beadScale * radiusScale * appearance[i].scaleFactor;
      visible[i] = beadVisible(kind[i], appearance[i], display) ? 1 : 0;
    }
    const real = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      if (kind[i] !== KIND.OR || parent[i] < 0) continue;
      real.copy(centres[i]);
      orientMarker(centres[i], centres[parent[i]], real, radii[parent[i]]);
    }
    return { centres, radii, visible };
  }, [ready, n, topData, positions, boxSize, display, radiusScale, appearance]);

  const writeBead = useMemo(() => (i, dummy, setColor) => {
    if (!layout.visible[i]) return false;
    dummy.position.copy(layout.centres[i]);
    dummy.scale.setScalar(layout.radii[i]);
    setColor(appearance[i].color ?? kindColors[topData.kind[i]]);
    return true;
  }, [layout, appearance, kindColors, topData]);

  const scratch = useMemo(cylinderScratch, []);
  const writeBond = useMemo(() => (b, dummy, setColor) => {
    const type = topData.bondType[b];
    if (!display.bondTypes[BOND_NAMES[type]]) return false;
    const i = topData.bonds[2 * b];
    const j = topData.bonds[2 * b + 1];
    if (!layout.visible[i] || !layout.visible[j]) return false;
    const thin = Math.min(appearance[i].scaleFactor, appearance[j].scaleFactor);
    const thickness = (type === BOND.ORIENT ? ORIENT_THICKNESS : BOND_THICKNESS) * radiusScale * thin;
    if (!cylinderBetweenPoints(dummy, scratch, layout.centres[i], layout.centres[j], thickness)) return false;
    setColor(bondColors[type]);
    return true;
  }, [topData, display, layout, appearance, radiusScale, scratch, bondColors]);

  // A bead that is not drawn cannot be clicked.
  const resolveIndex = useCallback(
    (instanceId) => (layout?.visible[instanceId] ? instanceId : null), [layout]);
  useRegisterPickable('mrdna-beads', { meshRef: beadMeshRef, resolveIndex, enabled: ready });

  if (!ready) return null;
  return (
    <>
      <InstancedLayer
        ref={beadMeshRef}
        geometry={beadGeometry}
        material={material}
        count={n}
        write={writeBead}
        deps={[writeBead]}
      />
      <InstancedLayer
        geometry={bondGeometry}
        material={bondMaterial}
        count={bondCount}
        write={writeBond}
        deps={[writeBond]}
      />
    </>
  );
}

export default MrdnaBeads;
