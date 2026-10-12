import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MrdnaPanel from '.';
import { useParticleStore } from '../../store/particleStore';
import { useUIStore } from '../../store/uiStore';

const TOP_DATA = {
  format: 'mrdna',
  counts: {
    beads: { ds: 162, ss: 36, or: 162, bead: 0 },
    bonds: { helix: 144, crossover: 0, ss: 0, junction: 72, orient: 162, bond: 0 },
  },
};

// Testing Library 13 calls react-dom/test-utils' act under React 18.3, which
// prints a one-off deprecation notice on the first render. It says nothing about
// this panel, so drop that one message and let every other error through.
let consoleError;
beforeAll(() => {
  const real = console.error;
  consoleError = jest.spyOn(console, 'error').mockImplementation((...args) => {
    if (String(args[0]).includes('ReactDOMTestUtils.act')) return;
    real(...args);
  });
});
afterAll(() => consoleError.mockRestore());

// Reset before each test rather than inside it: nothing is mounted yet, so the
// store write cannot trigger an update outside act.
beforeEach(() => {
  useParticleStore.setState({ topData: TOP_DATA });
  useUIStore.setState({
    showMrdnaPanel: true,
    mrdnaDisplay: {
      showOrient: true,
      beadScale: 1,
      bondTypes: { helix: true, crossover: true, ss: true, junction: true, orient: true, bond: true },
    },
  });
});

describe('MrdnaPanel', () => {
  it('lists the kinds and bond types present, with their counts', () => {
    render(<MrdnaPanel />);
    expect(screen.getByText('Double-stranded')).toBeInTheDocument();
    // ds beads, orientation beads and orient bonds all number 162.
    expect(screen.getAllByText('162')).toHaveLength(3);
    expect(screen.getByText('Junction')).toBeInTheDocument();
    // Absent types are not offered.
    expect(screen.queryByText('Crossover')).toBeNull();
  });

  it('switches a bond type and orientation beads in the store', () => {
    render(<MrdnaPanel />);
    fireEvent.click(screen.getByRole('checkbox', { name: /Helix/ }));
    expect(useUIStore.getState().mrdnaDisplay.bondTypes.helix).toBe(false);
    fireEvent.click(screen.getByRole('checkbox', { name: /Orientation beads/ }));
    expect(useUIStore.getState().mrdnaDisplay.showOrient).toBe(false);
  });

  it('sets the bead size', () => {
    render(<MrdnaPanel />);
    fireEvent.change(screen.getByRole('slider', { name: 'Bead size' }), { target: { value: '0.5' } });
    expect(useUIStore.getState().mrdnaDisplay.beadScale).toBe(0.5);
  });

  it('renders nothing for other formats or when closed', () => {
    useParticleStore.setState({ topData: { format: 'lorenzo' } });
    const { container } = render(<MrdnaPanel />);
    expect(container).toBeEmptyDOMElement();
  });
});
