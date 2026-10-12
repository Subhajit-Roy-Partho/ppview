import { renderHook } from '@testing-library/react';
import useParticleShift from './useParticleShift';
import { useParticleStore } from '../store/particleStore';

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

const BOX = [10, 10, 10];
const start = () => [{ x: 9, y: 1, z: 1 }, { x: 5, y: 5, z: 5 }];

const shiftX = (topData, delta) => {
  useParticleStore.setState({ positions: start(), currentBoxSize: BOX, topData });
  const { result } = renderHook(() => useParticleShift({ invalidateScene: () => {} }));
  result.current('x', delta);
  return useParticleStore.getState().positions.map(p => p.x);
};

describe('useParticleShift', () => {
  it('wraps into the box for a periodic format', () => {
    expect(shiftX({ format: 'lorenzo' }, 2)).toEqual([1, 7]);
    expect(shiftX(null, 2)).toEqual([1, 7]);
  });

  it('only translates for mrdna, whose box is synthetic', () => {
    expect(shiftX({ format: 'mrdna' }, 2)).toEqual([11, 7]);
    expect(shiftX({ format: 'mrdna' }, -20)).toEqual([-11, -15]);
  });
});
