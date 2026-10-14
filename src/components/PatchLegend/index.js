import React from 'react';
import { getColorForPatchID } from '../../utils/colorUtils';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';
import './PatchLegend.css';

function PatchLegend() {
  const topData = useParticleStore(state => state.topData);
  const currentColorScheme = useUIStore(state => state.currentColorScheme);
  
  if (!topData || !topData.particleTypes) return null;
  
  // Formats whose patch colour means something (PHB) supply their own legend.
  if (topData.patchLegend?.length) {
    return (
      <div className="patch-legend">
        <h3>Patch colours</h3>
        <ul>
          {topData.patchLegend.map(({ key, label, hex }) => (
            <li key={key}>
              <span className="color-box" style={{ backgroundColor: hex }}></span>
              <span>{label}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  const patchIDs = topData.particleTypes.flatMap((type) => type.patches);
  // Remove duplicates
  const uniquePatchIDs = [...new Set(patchIDs)];

  return (
    <div className="patch-legend">
      <h3>Patch Legend</h3>
      <ul>
        {uniquePatchIDs.map((id) => (
          <li key={id}>
            <span
              className="color-box"
              style={{ backgroundColor: getColorForPatchID(id, currentColorScheme).getStyle() }}
            ></span>
            <span>Patch ID: {id}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PatchLegend;