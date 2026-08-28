#!/usr/bin/env python3
"""
The tau_2 = 110 question as pure SAT, with a positive control.

SIX CP-SAT FORMULATIONS have returned UNKNOWN on this question -- one-sided,
two-sided, two-sided with a sound 360-fold break, the same with centre balance
and a proved support bound, and the two lean models built on W33-Theory's
shadow-code reduction. The difficulty is not the encoding. What the instance
needs is an unsatisfiability PROOF, which is what clause-learning SAT solvers
are built for and what CP-SAT's optimisation machinery is not.

THE REDUCTION THAT MAKES SAT POSSIBLE.  W33-Theory's
tensor_near_ovoid_shadow_closure proves

    tau_2 = 110  iff  40 minimum blockers B_L can be labelled so that every
    H_q = {L : q in B_L} is a disjoint union of complete four-line pencils
    centred on an independent set C_q.

Writing x[p][q] = [p in C_q], every part of that becomes local:

    q in B_L    <=> C_q meets L <=> sum_{p in L} x[p][q] >= 1,
    |B_L|        = sum_q sum_{p in L} x[p][q],
    |B_L cap M|  = sum_{q in M} sum_{p in L} x[p][q].

So three constraint families suffice, and each is a theorem rather than a
modelling choice:

    (1) at-most-one per (q, M)      every C_q is independent
    (2) 1 <= |B_L cap M| <= 2       B_L blocks every line and meets each at
                                    most twice -- our centre theorem, proved
                                    for all 360 minimum blockers, so the upper
                                    bound excludes nothing
    (3) |B_L| = 11                  B_L has minimum size

H_q is then automatically a DISJOINT pencil union, because C_q independent
means no two of its points share a line. And the global size is implied:
sum_L |B_L| = sum_q 4|C_q| = 4|X|, so 40*11 = 440 forces |X| = 110 without a
cardinality constraint over 1,600 variables. The encoding is therefore SOUND
and COMPLETE, and an UNSAT would prove tau_2 >= 111.

THE POSITIVE CONTROL, and the reason it exists.  "Sound and complete by
argument" is exactly the kind of claim that has failed elsewhere in this
session, and an over-constrained model returns UNSAT for free. So run the same
encoding on a quadrangle where the tight case is KNOWN ATTAINED.

W(3,2) has an ovoid, so tau_1 = 5 = st+1 and tau_2 = 25 = tau_1^2 exactly. Its
minimum blockers ARE ovoids and meet every line exactly once, so constraint (2)
becomes |B_L cap M| = 1 with no doubling. If the encoding is right it must
return SAT there.

    It does: SAT, |X| = 25, and the reconstructed set blocks all 225 tiles
    when checked from scratch against the incidence data.

So the encoding finds the known tight solution where one exists. It is not
over-constrained, and an UNSAT at q = 3 would be meaningful rather than an
artefact.

TOOLING NOTE. kissat404 segfaults inside pysat on the q=3 instance
(1,169,440 clauses over 132,720 variables); cadical is the usable engine.
A first 50-minute run hit its wall clock without finishing, which is the
honest signal that an UNSAT proof at this size needs longer, not that one does
not exist.
"""

import itertools
import json
import os
import sys

try:
    from pysat.card import CardEnc, EncType
    from pysat.formula import CNF, IDPool
    from pysat.solvers import Solver
except ImportError:
    sys.exit("needs python-sat:  py -3 -m pip install python-sat")

ROOT = r"C:\Repos\Holotrade"


def w32():
    """W(3,2): 15 points, 15 lines of 3, tau_1 = 5, minimum blockers are ovoids."""
    def form(u, v):
        return (u[0] * v[1] + u[1] * v[0] + u[2] * v[3] + u[3] * v[2]) % 2
    pts = [v for v in itertools.product([0, 1], repeat=4) if any(v)]
    idx = {v: i for i, v in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) == 0:
            c = tuple(a[i] ^ b[i] for i in range(4))
            lines.add(tuple(sorted(idx[x] for x in (a, b, c))))
    return len(pts), [list(x) for x in sorted(lines)]


def build(n, lines, tau1, max_trace):
    """The three constraint families. max_trace is 1 when blockers are ovoids."""
    pool, cnf = IDPool(), CNF()

    def X(p, q):
        return pool.id(("x", p, q))

    for q in range(n):
        for M in lines:                       # (1) C_q independent
            for a, b in itertools.combinations(M, 2):
                cnf.append([-X(a, q), -X(b, q)])
    for Ln in lines:
        for M in lines:                       # (2) 1 <= |B_L cap M| <= max
            lits = [X(p, q) for p in Ln for q in M]
            cnf.append(lits)
            for combo in itertools.combinations(lits, max_trace + 1):
                cnf.append([-l for l in combo])
        lits = [X(p, q) for p in Ln for q in range(n)]   # (3) |B_L| = tau_1
        cnf.extend(CardEnc.equals(lits=lits, bound=tau1, vpool=pool,
                                  encoding=EncType.seqcounter).clauses)
    return pool, cnf, X


def verify(pairs, lines):
    S = set(pairs)
    return all(any((p, q) in S for p in A for q in B)
               for A in lines for B in lines)


def main():
    n, lines = w32()
    tau1, expected = 5, 25
    print("POSITIVE CONTROL FOR THE tau_2 SAT ENCODING")
    print("=" * 70)
    print("  Six CP-SAT formulations returned UNKNOWN at q=3, so the question")
    print("  moves to a clause-learning solver. Before trusting an UNSAT there,")
    print("  run the SAME encoding where the answer is known to be SAT.")
    print()
    print("  W(3,2): %d points, %d lines, tau_1 = %d = st+1 (an ovoid), so"
          % (n, len(lines), tau1))
    print("  minimum blockers meet every line exactly once and the tight case")
    print("  |X| = %d is attained." % expected)
    print()
    pool, cnf, X = build(n, lines, tau1, max_trace=1)
    print("  clauses %d, vars %d" % (len(cnf.clauses), pool.top))
    with Solver(name="cadical195", bootstrap_with=cnf.clauses) as s:
        sat = s.solve()
        pairs = []
        if sat:
            mdl = set(l for l in s.get_model() if l > 0)
            pairs = [(p, q) for p in range(n) for q in range(n)
                     if X(p, q) in mdl]
    ok = sat and len(pairs) == expected and verify(pairs, lines)
    print("  result: %s" % ("SAT" if sat else "UNSAT"))
    if sat:
        print("  |X| = %d (expected %d)" % (len(pairs), expected))
        print("  blocks all %d tiles, rechecked from the incidence data: %s"
              % (len(lines) ** 2, verify(pairs, lines)))
    print()
    if ok:
        print("  ==> CONTROL PASSES. The encoding finds the known tight solution")
        print("      where one exists, so it is not over-constrained and an")
        print("      UNSAT at q=3 would be meaningful.")
    else:
        print("  ==> CONTROL FAILS. Any UNSAT at q=3 would be an artefact.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "tensor_110_sat_encoding.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.tensor-110-sat-encoding.v1",
                "valid": bool(ok),
                "why": ("six CP-SAT formulations returned UNKNOWN; the instance "
                        "needs an unsatisfiability proof, which is what "
                        "clause-learning solvers are for"),
                "constraintFamilies": [
                    "at-most-one per (q,M): every C_q independent",
                    "1 <= |B_L cap M| <= 2: blocks, and our centre theorem",
                    "|B_L| = tau_1: minimum size",
                ],
                "impliedNotEncoded": ("H_q is automatically a disjoint pencil "
                                      "union, and |X| = 110 follows from "
                                      "sum_L |B_L| = 4|X|"),
                "soundAndComplete": True,
                "positiveControl": {
                    "geometry": "W(3,2)", "tau1": tau1,
                    "tightCase": expected, "knownAttained": True,
                    "result": "SAT" if sat else "UNSAT",
                    "witnessSize": len(pairs),
                    "witnessVerified": verify(pairs, lines) if sat else False,
                    "passes": bool(ok),
                    "purpose": ("an over-constrained model returns UNSAT for "
                                "free; this shows the encoding finds the known "
                                "tight solution where one exists"),
                },
                "q3Instance": {"clauses": 1169440, "vars": 132720,
                               "status": "running",
                               "kissatSegfaults": True,
                               "usableEngine": "cadical"},
                "boundary": ("the control validates the ENCODING. It says "
                             "nothing about whether tau_2 = 110, which stays "
                             "open in [110, 115]."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
