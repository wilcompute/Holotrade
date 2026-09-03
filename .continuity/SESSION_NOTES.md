# Session notes — 2026-09-03

## Goal

Reconcile both live repositories, correct the W33 obstruction carrier, prove the
two-carrier common quotient and fibre-product bridge in GAP, expose the result as
a fail-closed hardware contract, then identify whether the fibre stabilizer has
a native protected-qutrit action and publish the evidence through HoloTrade.

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
- The fibre stabilizer's `F20 = AGL(1,5)` presentation now acts explicitly on
  the cyclic `[[5,1,3]]_3` qutrit block. Bare coordinate permutations expose
  only `D10`; five determinant-one local qutrit Clifford maps restore the
  missing order-four affine multiplier.
- The presentation is matched generator by generator: the fibre action and the
  physical ten-dimensional Pauli lift both satisfy
  `T^5 = M^4 = 1` and `M T M^-1 = T^3`.
- GAP freezes the faithful action on `5 x 8 = 40` addressed nonidentity
  one-qutrit Paulis. Generated RTL implements those two transition tables.
- Yosys proves closure and all three presentation laws for every valid address;
  replacing the Clifford-compensated multiplier by identity produces the
  intended SAT counterexample.

## Validation

- Five-front GAP/Node freezer: PASS, source-bound SHA-256
  `57b1ead2bb8255f2170b3c9e915820211c5083e080695dce97d2ab1f882eda9f`.
- Yosys formal freezer: PASS; positive UNSAT and unsafe control SAT; SHA-256
  `03a5c46a1dbe05b59307c49142833657557c9a1c6d3d2d88fde3d93bcbb9fbce`.
- F20/qutrit GAP/Node freezer: PASS; D10 versus F20 and physical Pauli lift;
  SHA-256 `3f30670ca5d31aedd8cd1dca785c05a75de125222184fe48b794530be3c47e99`.
- F20/qutrit Yosys freezer: PASS; 1,950-variable positive proof and
  234-variable mutation counterexample; SHA-256
  `fae8ad400d906a408195b7a790e267fbbc3ff0b4a6ec45c68d2599821738ad5b`.
- Focused F20/qutrit contract tests: 4/4 PASS.
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
- W33 Pass 79 owns the cyclic five-qutrit code; W33 commits `94cf718a0` and
  `df284a029` own the singular-K12 `[[66,8,3]]_3` storage result and bare-handoff
  no-go. The new result is the explicit router-stabilizer/code-automorphism
  interface, not a local or fault-tolerant recode.

## Publication state

The base theorem packet is committed on `codex-five-front-router` as `bec0d62`
with handoff commit `a404f5a`. The F20/qutrit packet, updated documentation, and
integration with current `origin/master` remain to be committed and pushed.
