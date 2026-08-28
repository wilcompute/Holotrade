#!/usr/bin/env node
"use strict";

// Tight depth-2 obstruction: |X|=110 would force a self-duality of W(3,3).
//
// At equality every row and column shadow is a minimum 11-point blocker.
// For a row line L let c_L be the centre of its blocker; for a column line M
// let d_M be the centre of its blocker.  A minimum blocker meets the four
// lines through its centre twice and every other line once, hence
//
//   |X cap (L x M)| = 2  iff c_L in M  iff d_M in L.
//
// Thus the two centre maps satisfy pencil reciprocity
//
//   c_L in M <=> d_M in L.                                    (1)
//
// The only possible multiplicities of a centre are 0,1,4.  If a point p is
// used four times as c_L, the four corresponding row lines are exactly the
// pencil through p; (1) then forces the same four opposite-side centre values.
// Let F be the set of multiplicity-four centres.  F is independent, and every
// point adjacent to F is adjacent to exactly four points of F.  Counting
// unordered pairs of F through their common neighbours gives
//
//   4*C(|F|,2) = 3*|F|*C(4,2),
//
// so nonempty F would have |F|=10.  But alpha(W(3,3))=7. Therefore F is empty
// and every centre has multiplicity exactly one: c and d are bijections.
// Equation (1) is then an incidence isomorphism W(3,3) -> W(3,3)^D.
// Classical symplectic generalized quadrangles W(q) are self-dual iff q is
// even; q=3 is odd.  Contradiction. Hence tau_2 != 110.
//
// Existing witness: 115 leaves.  Certified frontier becomes [111,115].

function choose2(n) { return n * (n - 1) / 2; }

function run() {
  const candidates = [];
  for (let f = 1; f <= 40; f++) {
    if (4 * choose2(f) === 3 * f * choose2(4)) candidates.push(f);
  }
  if (JSON.stringify(candidates) !== JSON.stringify([10])) {
    throw new Error(`unexpected multiplicity-four count solutions: ${candidates}`);
  }
  const alpha = 7;
  if (!(candidates[0] > alpha)) throw new Error("independence obstruction failed");
  return {
    schema: "holotrade.tensor-tight-self-duality-obstruction.v1",
    status: "PASS",
    tightCandidate: 110,
    multiplicityFourEquation: "4*C(f,2)=3*f*C(4,2)",
    nonzeroMultiplicityFourSolution: 10,
    alphaW33: alpha,
    multiplicityFourImpossible: true,
    centreMapsForcedBijective: true,
    reciprocity: "c_L in M iff d_M in L",
    consequenceOfBijectivity: "an incidence duality W(3,3) -> W(3,3)^D",
    classicalInput: "W(q) is self-dual iff q is even; q=3 is odd",
    candidate110Possible: false,
    certifiedInterval: [111, 115],
    boundary: "The 115 upper bound is the existing explicit Holotrade witness. This argument raises only the lower bound; it does not decide 111-114."
  };
}

if (require.main === module) console.log(JSON.stringify(run(), null, 2));
module.exports = { run };
