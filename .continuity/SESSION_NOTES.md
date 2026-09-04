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
- The same inner fibre `F20` has slow-target orbits `[5,10,10,20]`. Its unique
  five-orbit is a coclique whose set stabilizer induces `S5`; the orbit of such
  five-sets has size 216, and the fixed qutrit presentation admits exactly one
  site-to-circuit map.
- A different five-state geometry lives on a `GQ(4,2)` ROM line. Its inner line
  stabilizer has image `A5`, its full `W(E6)` stabilizer has image `S5`, and the
  unique line-preserving `F20` complement meets the inner group in exactly the
  bare `D10` subgroup.
- The 40 protected Pauli addresses and 40 Payne axes are each two regular
  `F20` orbits, giving exactly 800 equivariant bijections. Exhausting all 20
  presentation-compatible `F20` isomorphisms and all 16,000 induced maps finds
  no map that also welds every site's eight addresses to the eight Payne covers
  through its matched circuit target.
- That no-go has a complete two-point defect spectrum: 9,600 candidates match
  no address incidences, while 6,400 match exactly four of eight at every site.
  The optimum is uniformly half-incidence (20/40), never an uneven near-weld.
- The frozen zero-match gauge composes with the production Payne catalogue so
  every address reaches an axis covering its matched circuit target in exactly
  one W33-collinearity hop. The composition is deterministic but not the
  prohibited direct equivariant weld and remains non-dispatchable.
- The runtime codec therefore exposes the selected reproducible address map as
  a noncanonical gauge and returns `dispatchable: false`; this exact finite
  atlas is not presented as a fault-tolerant recode or physical route.

## Validation

- Five-front GAP/Node freezer: PASS, source-bound SHA-256
  `57b1ead2bb8255f2170b3c9e915820211c5083e080695dce97d2ab1f882eda9f`.
- Yosys formal freezer: PASS; positive UNSAT and unsafe control SAT; SHA-256
  `03a5c46a1dbe05b59307c49142833657557c9a1c6d3d2d88fde3d93bcbb9fbce`.
- F20/qutrit GAP/Node freezer: PASS; D10 versus F20 and physical Pauli lift;
  canonical certificate SHA-256
  `e8d7044c15eaba12ae115c4e1c0ca420ac349514ac06571e2042b095be730b3b`.
- F20/qutrit Yosys freezer: PASS; 1,950-variable positive proof and
  234-variable mutation counterexample; canonical certificate SHA-256
  `eafbd89cb2db7d5e1e9430750e55438864bda671eb0be3b29cfe36e58fc429da`.
- Focused F20/qutrit contract tests: 5/5 PASS, including documentation and
  live-site publication surfaces.
- Full exact backend regeneration reached 77/78 before exposing a stale
  dual-carrier source hash caused by the representation-canonicality rewrite;
  the dual-carrier formal certificate was regenerated without weakening its
  Yosys proof or mutation control, and its focused lane is now 5/5 PASS.
- JavaScript syntax and JSON parsing: PASS.
- `docs/holotrade.tex` compiles to `docs/holotrade.pdf` with warnings only.
- F20/Payne GAP regeneration and focused Node contract: 6/6 PASS; certificate
  SHA-256 `1153ae29ea6df5ff8d299b406fa864d01233662c37f67667ed089afe3cd4f099`.
- Certificate source hashing now canonicalizes CRLF to LF before SHA-256, so
  Windows and GitHub Actions bind the same source text without weakening any
  theorem value.
- Full 84-test backend first pass: 83/84 mathematical and runtime tests passed;
  the sole failure was an unchanged boundary sentence split between JavaScript
  literals. The literal was rejoined; the focused atlas lane is now 6/6 and the
  dependent protected-qutrit lane is 5/5.
- The updated paper compiles to a 258.41 KiB PDF with only pre-existing
  fontconfig and underfull-box warnings; JavaScript syntax and workflow YAML
  structure validate.
- Focused CI installs GAP/GRAPE and checks both exact regeneration and runtime
  adapter syntax on pull requests and `master` pushes.

## Reconciliation

- HoloTrade `origin/master` was fetched through GitKraken. The base theorem and
  first F20 bridge packet were merged at `ea0ce53`; the later 31-commit delta
  adds the projective 45-slot slow path, `GQ(4,2)` ROM, 1296-state fibre
  hypervisor, capability machine, and 27-state Pauli-torsor theorem without
  modifying this packet's publication paths.
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
with handoff commit `a404f5a`. The completed F20/qutrit publication packet was
merged to `master` at `7acbb22466de0817753194f93f4afb5493657673`. The current
`codex-f20-gq-line-outer` packet adds the GAP-owned two-geometry atlas, exact
800-map count and 0/16,000 compatibility boundary, fail-closed codec, focused
CI, and synchronized README, paper, PDF, and website evidence surfaces. Pull
request #3 is open; its only observed CI failure was the now-repaired CRLF/LF
source-hash portability mismatch.
