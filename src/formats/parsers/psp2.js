import { parseSRSSpringsTopology } from './srsSprings';

// PSP2 format is structurally identical to SRS Springs (PSP1).
// Spring vectors are in the particle's local frame (used for orientation torques),
// but for visualization purposes the topology is parsed the same way.
export const parsePSP2Topology = (content) => {
  const result = parseSRSSpringsTopology(content);
  return { ...result, format: 'psp2' };
};
