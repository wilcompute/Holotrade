# Session notes — 2026-09-02

## Goal

Reconcile both live repositories, correct the W33 obstruction carrier, prove the
two-carrier common quotient and fibre-product bridge in GAP, expose the result as
a fail-closed hardware contract, and publish the evidence through HoloTrade's
README, paper, website, tests, and frozen certificates.

## Current result

- The obstruction carrier is `27 completion charts x 40 W33 lines`, not the
  earlier point-product surrogate.
- Its explicit Steinberg transfer to the 216-state target has rank 3.
- The two nonconjugate S5 carriers share a canonical 36-state quotient; the
  minimum cross-relation is 36 disjoint `K(6,6)` components.
- Their fibre product has degree 1296 and point stabilizer `F20 = C5:C4`.
- The fibre product and corrected obstruction each contain the 81- and
  64-dimensional building modules with multiplicity 3, so their common
  building block has dimension 435 and cross-Hom dimension 18.
- The dual-carrier RTL preserves native carrier type and permits only the
  36-state quotient to cross the fork. Yosys proves the positive design and
  finds the intended counterexample in the unsafe control.
- The tau2 defect audit excludes an eleven-triple descent of the 115 witness
  but correctly leaves the certified interval `[111,115]` open.

## Validation

- GAP/Node freezer: PASS, source-bound SHA-256
  `fc65bf978e2a910e2e6f0567c72afad2ca68f4aa65b0c8fd19ad7164d8e445d7`.
- Yosys formal freezer: PASS; positive UNSAT and unsafe control SAT; SHA-256
  `03a5c46a1dbe05b59307c49142833657557c9a1c6d3d2d88fde3d93bcbb9fbce`.
- Focused contract tests: 5/5 PASS.
- JavaScript syntax and JSON parsing: PASS.
- `docs/holotrade.tex` compiles to `docs/holotrade.pdf` with warnings only.

## Reconciliation

- HoloTrade `origin/master` was fetched through GitKraken. Its commits after
  this worktree's base touch attestation, storage, placement, and depth-5 K14
  files, not this packet's changed paths.
- W33-Theory `origin-https/master` was fetched through GitKraken and reviewed
  read-only because that checkout contains a large parallel dirty tree.
- Existing W33 universal-VM, heterogeneous-IPC, checkpoint, and modular M3
  results are cited as prior art. The additive result here is the corrected
  line carrier plus the exact `1296/F20/3+3/435/18` fibre-product bridge and its
  HoloTrade hardware/publication surface.

## Publication state

The theorem packet is committed on `codex-five-front-router` as `bec0d62`.
The complete backend regression passed 73/73. Integration with current
`origin/master` and the final GitKraken push remain.
