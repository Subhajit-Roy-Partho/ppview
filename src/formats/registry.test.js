import { rendererFor, getFormat } from './registry';
import MrdnaBeads from '../components/MrdnaBeads';

describe('registry', () => {
  it('draws an mrdna model with the bead renderer', () => {
    expect(rendererFor({ format: 'mrdna' })).toBe(MrdnaBeads);
    expect(getFormat('mrdna').label).toBe('mrdna beads');
  });
});
