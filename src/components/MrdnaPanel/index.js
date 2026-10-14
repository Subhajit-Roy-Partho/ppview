import React from 'react';
import DraggablePanel from '../DraggablePanel';
import { CloseIcon } from '../Icons';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';
import {
  KIND, KIND_NAMES, KIND_LABELS, BOND_NAMES, BOND_LABELS,
} from '../../formats/parsers/mrdna';
import { MRDNA_COLORS } from '../MrdnaBeads/geometry';

const Swatch = ({ color }) => <span className="mrdna-swatch" style={{ background: color }} aria-hidden="true" />;

/** What the mrdna renderer draws, with a legend that is also its controls. */
function MrdnaPanel() {
  const topData = useParticleStore(state => state.topData);
  const show = useUIStore(state => state.showMrdnaPanel);
  const setShow = useUIStore(state => state.setShowMrdnaPanel);
  const display = useUIStore(state => state.mrdnaDisplay);
  const setShowOrient = useUIStore(state => state.setMrdnaShowOrient);
  const setBeadScale = useUIStore(state => state.setMrdnaBeadScale);
  const setBondType = useUIStore(state => state.setMrdnaBondType);

  if (topData?.format !== 'mrdna' || !show) return null;
  const { beads, bonds } = topData.counts;

  return (
    <DraggablePanel initialX={20} initialY={20} className="pp-panel mrdna-panel" storageId="mrdna">
      <div className="panel-header drag-handle" tabIndex={0}>
        <h3 className="panel-title">mrdna beads</h3>
        <button className="icon-button" onClick={() => setShow(false)} title="Hide mrdna panel" aria-label="Hide mrdna panel">
          <CloseIcon size={15} />
        </button>
      </div>
      <div className="panel-body">
        <section className="panel-section" aria-label="Beads">
          <h4 className="mrdna-heading">Beads</h4>
          <ul className="mrdna-legend">
            {KIND_NAMES.map((name, k) => beads[name] > 0 && (
              <li key={name}>
                {k === KIND.OR ? (
                  <label>
                    <input type="checkbox" checked={display.showOrient} onChange={e => setShowOrient(e.target.checked)} />
                    <Swatch color={MRDNA_COLORS.kind[k]} />
                    <span>{KIND_LABELS[k]} beads</span>
                  </label>
                ) : (
                  <span className="mrdna-legend-label">
                    <Swatch color={MRDNA_COLORS.kind[k]} />
                    <span>{KIND_LABELS[k]}</span>
                  </span>
                )}
                <span className="num">{beads[name]}</span>
              </li>
            ))}
          </ul>
          <label className="mrdna-slider">
            <span>Bead size</span>
            <input
              type="range" min="0.1" max="2" step="0.05"
              value={display.beadScale}
              onChange={e => setBeadScale(parseFloat(e.target.value))}
              aria-label="Bead size"
            />
            <span className="num">{display.beadScale.toFixed(2)}×</span>
          </label>
          {beads.or > 0 && (
            <p className="section-hint">
              Orientation beads sit 1.5 Å off the helix axis, inside their bead. They are drawn
              just outside it, on a short stalk, in the direction they point.
            </p>
          )}
        </section>
        <section className="panel-section" aria-label="Bonds">
          <h4 className="mrdna-heading">Bonds</h4>
          <ul className="mrdna-legend">
            {BOND_NAMES.map((name, t) => bonds[name] > 0 && (
              <li key={name}>
                <label>
                  <input type="checkbox" checked={display.bondTypes[name]} onChange={e => setBondType(name, e.target.checked)} />
                  <Swatch color={MRDNA_COLORS.bond[t]} />
                  <span>{BOND_LABELS[t]}</span>
                </label>
                <span className="num">{bonds[name]}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </DraggablePanel>
  );
}

export default MrdnaPanel;
