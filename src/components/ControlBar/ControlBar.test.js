import React from 'react';
import { render, screen } from '@testing-library/react';
import ControlBar from '.';
import { useParticleStore } from '../../store/particleStore';

// Only the part of the bar under test is real; every other prop is inert.
const noop = () => {};
const props = {
  isControlsVisible: true, setIsControlsVisible: noop,
  isPlaying: false, togglePlayback: noop, resetTrajectory: noop, stepFrame: noop,
  currentConfigIndex: 0, totalConfigs: 1, currentTime: 0, currentEnergy: 0,
  playbackSpeed: 1, setPlaybackSpeed: noop, isSpeedPopupVisible: false,
  setIsSpeedPopupVisible: noop, speedPopupRef: { current: null },
  handleSliderChange: noop, sphereSegments: 16, setSphereSegments: noop,
  particleRadius: 0.5, handleRadiusChange: noop,
};

// Testing Library 13 calls react-dom/test-utils' act under React 18.3, which
// prints a one-off deprecation notice on the first render; drop only that.
let consoleError;
beforeAll(() => {
  const real = console.error;
  consoleError = jest.spyOn(console, 'error').mockImplementation((...args) => {
    if (String(args[0]).includes('ReactDOMTestUtils.act')) return;
    real(...args);
  });
});
afterAll(() => consoleError.mockRestore());

describe('ControlBar colour scheme', () => {
  it('is offered for formats whose colours it drives', () => {
    useParticleStore.setState({ topData: { format: 'lorenzo' } });
    render(<ControlBar {...props} />);
    expect(screen.getByTitle('Particle color scheme')).toBeInTheDocument();
  });

  it('is hidden for mrdna, whose bead and bond colours are fixed', () => {
    useParticleStore.setState({ topData: { format: 'mrdna' } });
    render(<ControlBar {...props} />);
    expect(screen.queryByTitle('Particle color scheme')).toBeNull();
  });
});
