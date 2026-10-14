# mrdna Bead Model Support in ppview

## Overview

ppview reads the bead model and Brownian-dynamics trajectory written by the
mrdna engine, a re-implementation of the MrDNA multi-resolution coarse-grained
DNA model (Maffeo & Aksimentiev, *NAR* 48:5135, 2020) used to relax oxDNA
designs quickly. Each double-stranded bead stands for *res* base pairs
(5, 3 or 1 bp/bead), each single-stranded bead for *res* nucleotides, and each
double-stranded bead carries an orientation bead that encodes the local twist.

## Files

Drop the files of one run together. They share a name stem (`X`):

| file | content | needed |
|---|---|---|
| `X.model` | the bead model: positions, nucleotides per bead, bonds, angles, dihedrals, exclusions | yes |
| `X.traj` | every Brownian-dynamics frame written during the run | one of these, or neither |
| `X.final` | the last frame only | |
| `X.energy` | one line per `.traj` frame: `step E_total E_bond E_angle E_dihedral E_nonbonded` | optional |

All binary data is little-endian `f64`; lengths are Å, energies kcal/mol.

- `.model` is recognised by its magic number (`0x4D52444E4131`) whatever its name.
- `.traj` and `.final` are recognised by their extension **and** a binary head,
  so a text oxDNA trajectory named `trajectory.traj` still loads as oxDNA.
- `.energy` is recognised by its `# step E_total` header.
- When several runs are dropped at once, the frames sharing the model's name
  stem are used.

## What is shown

- **Frame 0** is the model's own positions: the bead mapping of the design,
  before minimisation. Frames 1… are the `.traj` frames (or the `.final`
  frame). The readout shows each frame's step and total energy from `.energy`.
- **Beads** are spheres whose size follows the nucleotides they stand for:
  - double-stranded — blue
  - single-stranded — orange
  - orientation — small grey markers on a short stalk. The real orientation
    bead sits 1.5 Å off the helix axis, inside its bead; it is drawn just
    outside, in the direction it points. The selection panel reports its true
    position.
- **Bonds** are cylinders coloured by type: helix, crossover, single strand,
  junction and orientation.
- Coordinates are converted to oxDNA units (÷ 8.518). The model has no box, so
  one is made around frame 0. Frames are centred on their centroid and never
  wrapped, because wrapping would cut bonds; the shift keys translate without
  wrapping too.

## How kinds and bond types are recovered

The `.model` file stores numbers only — no labels — so ppview works them out
from the model's structure:

- an **orientation** bead is the only kind carrying no nucleotides;
- a **double-stranded** bead is one bonded to an orientation bead;
- every other bead is **single-stranded**;
- a bond between two double-stranded beads with a twist dihedral across it
  (orientation beads at both ends) runs along a **helix**; any other such bond
  is a **crossover**; a single–single bond is a **single strand** bond, and a
  double–single bond a **junction**.

These rules reproduce the mrdna Python model exactly, bead for bead and bond
for bond, at 5, 3 and 1 bp/bead. A model built without orientation beads gives
nothing to tell double from single strands, so its beads and bonds are labelled
plainly rather than guessed.

## The mrdna panel

Opens with an mrdna run (reopen it from **mrdna beads** in the Tools group):

- a legend with the count of each bead kind and bond type, listing only those
  present;
- checkboxes to show or hide orientation beads and each bond type — a bond is
  drawn only while both of its beads are;
- a bead-size slider.

Clicking a bead selects it; the selection panel shows e.g. `ds bead · 10 nt`.
Clustering, the Detail and radius controls and selection work on beads as on
any other particle. The colour-scheme selector is hidden, since bead and bond
colours carry their kind.

## Errors

ppview says what is wrong rather than failing silently:

- a file whose magic number is not mrdna's, or a model that ends early or has
  bytes left over;
- frames dropped without their `.model`;
- a `.traj` shorter than one frame of the model (it names the bead count it
  expected), or a `.final` that is not exactly one frame.

A `.traj` cut short mid-frame — a run that blew up stops mid-write — loads its
whole frames and ignores the tail.
