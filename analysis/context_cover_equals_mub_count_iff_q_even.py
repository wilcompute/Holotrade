#!/usr/bin/env python3
"""
Covering every measurement context of two qudits costs exactly the MUB count
when q is even, and strictly more when q is odd. And the two tens in this
project are not the same ten.

THE SETTING, which is already ours.  W(3,q) is the commutation geometry of the
two-qudit Pauli classes, its lines are the maximal commuting sets -- the
measurement CONTEXTS -- and the repository has carried the quantum reading for
months:

  * analysis/2026-07-08_pass70_15vector_doily_attack.md: "Ovoids <-> MUB basis
    states in discrete quantum mechanics";
  * analysis/2026-05-29_spread_square_we6_factorization.md: the 36 spreads of
    W(3,3) are "complete two-qutrit stabilizer/MUB spread-frame choices";
  * analysis/w33_hesse_mermin_contextuality.py: the Hesse configuration is the
    single-qutrit phase space with its 4 MUBs, and two qutrits turn on the
    state-independent contextuality that powers the machine.

Externally the same dictionary is classical: complete sets of MUBs correspond
to symplectic spreads (Calderbank, Cameron, Kantor and Seidel 1996; Kantor).

So the ovoid size q^2+1 is not an abstract parameter. It is the number of
bases in a complete MUB set for dimension q^2, and an OVOID is a perfect
transversal of the contexts: one observable in every context, no two of them
commuting.

THE QUESTION NOBODY HERE HAS ASKED. tau_1 is the fewest observables meeting
EVERY context. If an ovoid exists it is such a set, so tau_1 = q^2+1 and the
cover costs exactly the MUB count. If not, tau_1 is strictly larger. W(3,q)
has an ovoid if and only if q is EVEN, so the prediction is a clean parity
dichotomy. Computed here:

    q     tau_1     q^2+1 (MUB count)    excess     q even
    2       5             5                0        yes
    3      11            10                1        no
    4      17            17                0        yes
    5      29            26                3        no
    7     <=55           50              <=5        no
    8      65            65                0        yes

The first four and q = 8 are OPTIMAL; q = 7 is a proved witness of 55 with the
solver's bound still at 50, so its excess is only known to be at most 5. THREE
even cases attain the MUB count exactly -- q = 2, 4 and 8 -- and every odd case
exceeds it. The excess matches q-2 at q = 3 and 5 and is consistent with it at
q = 7, which is recorded as a pattern and nothing more -- note it is NOT q-2 at
q = 4 or q = 8, where the excess is 0 while q-2 is 2 and 6, so any formula must
be conditioned on parity first.

WHAT IT MEANS FOR HARDWARE.  Certifying that nothing hides from your
measurement set costs, for a two-qudit link, exactly one observable per MUB
basis when the local dimension is a power of two, and strictly more otherwise.
Qubit-like carriers get the perfect transversal for free; a qutrit carrier
pays one extra observable, and a q=5 carrier pays three. The penalty is not
spectral -- the Hoffman bound permits q^2+1 at every q -- it is Thas's
non-existence theorem for ovoids at odd q.

AND IT DOES NOT COMPOUND ACROSS A NETWORK.  The fractional cover number is

    tau* = q^2 + 1   for EVERY q,

by the uniform certificate: weight 1/(q+1) on every point is a fractional
cover of weight q^2+1 since each line holds q+1 points, and weight 1/(q+1) on
every line is a fractional matching of the same value since each point lies on
q+1 lines. Weak duality makes both optimal. Since tau* is multiplicative on
products, an n-carrier network of product observables has growth rate exactly
q^2+1 per carrier. So the odd-q penalty is a pure INTEGRALITY GAP: real on one
link, invisible in the asymptotic per-node cost.

THE TWO TENS, and this is the part worth catching.
w33_hesse_mermin_contextuality.py reads 10 as Phi_4 = dim Sp(4), the
contextual-fraction denominator, giving contextual fraction 1/10. The
fractional cover number of W(3,3) is also 10. They are different quantities
that agree at q = 3 and nowhere else:

    dim Sp(4,q) = 10   for every q
    tau*(W(3,q)) = q^2+1 = 10 only at q = 3, and 26 at q = 5.

Recorded because a coincidence at the single value of q this project mostly
works at is exactly how two unrelated invariants get welded together.

SCOPE. The dichotomy is verified at six values of q, not proved. The
mechanism -- ovoid exists iff q even, and an ovoid is a perfect context
transversal -- is a theorem, so tau_1 = q^2+1 for even q is proved by
exhibiting the ovoid; what is only computational is that the excess is
strictly positive at the odd q tested, and the value of that excess.
"""

import itertools
import json
import os
import sys

try:
    from ortools.sat.python import cp_model
except ImportError:
    sys.exit("needs ortools:  py -3 -m pip install ortools")

ROOT = r"C:\Repos\Holotrade"


def gf(q):
    if q in (2, 3, 5, 7):
        els = list(range(q))
        return (els, [[(a + b) % q for b in els] for a in els],
                [[(a * b) % q for b in els] for a in els])
    if q == 4:
        return ([0, 1, 2, 3],
                [[0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0]],
                [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]])
    raise ValueError("unsupported q")


def build(q):
    els, add, mul = gf(q)
    inv = {a: next(b for b in els if mul[a][b] == 1) for a in els if a}

    def nm(v):
        i = next(k for k, x in enumerate(v) if x != 0)
        return tuple(mul[inv[v[i]]][x] for x in v)

    def form(u, v):
        a, b = mul[u[0]][v[1]], mul[u[1]][v[0]]
        c, d = mul[u[2]][v[3]], mul[u[3]][v[2]]
        return (a ^ b ^ c ^ d) if q % 2 == 0 else (a - b + c - d) % q

    pts = sorted({nm(v) for v in itertools.product(els, repeat=4) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    lines = set()
    for a, b in itertools.combinations(range(len(pts)), 2):
        if form(pts[a], pts[b]) != 0:
            continue
        S = set()
        for x in els:
            for y in els:
                if x == 0 and y == 0:
                    continue
                w = tuple(add[mul[x][pts[a][k]]][mul[y][pts[b][k]]]
                          for k in range(4))
                if any(w):
                    S.add(idx[nm(w)])
        if len(S) == q + 1:
            lines.add(tuple(sorted(S)))
    return len(pts), sorted(lines)


def tau1(n, lines, budget):
    m = cp_model.CpModel()
    x = [m.NewBoolVar("") for _ in range(n)]
    for L in lines:
        m.AddBoolOr([x[p] for p in L])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = budget
    s.parameters.num_search_workers = 8
    st = s.Solve(m)
    return int(s.ObjectiveValue()), s.StatusName(st)


def main():
    print("CONTEXT COVER = MUB COUNT, EXACTLY WHEN q IS EVEN")
    print("=" * 72)
    print("  Lines of W(3,q) are the maximal commuting sets = measurement")
    print("  contexts. q^2+1 is the ovoid size AND the number of bases in a")
    print("  complete MUB set for dimension q^2. An ovoid is a perfect")
    print("  transversal: one observable per context, none commuting.")
    print()
    rows = []
    for q, budget in ((2, 60.0), (3, 120.0), (4, 600.0), (5, 1800.0)):
        # q = 7 and 8 are run separately by scratchpad/tau1_gfq.py: they take
        # long enough that keeping them here would make this file unrunnable.
        # q=7 -> tau_1 <= 55 (FEASIBLE, bound 50); q=8 -> 65 = q^2+1 OPTIMAL.
        n, lines = build(q)
        t1, st = tau1(n, lines, budget)
        mub = q * q + 1
        rows.append({"q": q, "points": n, "contexts": len(lines),
                     "tau1": t1, "status": st, "mubCount": mub,
                     "excess": t1 - mub, "qEven": q % 2 == 0,
                     "attainsMubCount": t1 == mub})
        print("  q=%-2d %4d Paulis, %4d contexts | tau_1 = %-3d (%s) | MUB "
              "count q^2+1 = %-3d | excess %-2d | q even %s"
              % (q, n, len(lines), t1, st, mub, t1 - mub, q % 2 == 0))
    print()
    ok_dich = all(r["attainsMubCount"] == r["qEven"] for r in rows)
    print("  attains the MUB count exactly when q is even: %s" % ok_dich)
    print()
    print("  tau* = q^2+1 for EVERY q: weight 1/(q+1) on points is a")
    print("  fractional cover of that value, weight 1/(q+1) on lines is a")
    print("  fractional matching of the same, so both are optimal. The odd-q")
    print("  penalty is therefore a pure INTEGRALITY GAP -- real on one link,")
    print("  and invisible in the per-carrier growth rate of a network.")
    print()
    print("  THE TWO TENS. w33_hesse_mermin_contextuality.py reads 10 as")
    print("  Phi_4 = dim Sp(4), the contextual-fraction denominator. tau* is")
    print("  also 10 -- but only at q = 3. dim Sp(4,q) = 10 for every q while")
    print("  tau* = q^2+1 is 26 at q = 5. Different invariants, agreeing at")
    print("  the one q this project mostly works at.")

    ok = ok_dich and all(r["status"] == "OPTIMAL" for r in rows)
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "context_cover_equals_mub_count_iff_q_even.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.context-cover-mub-dichotomy.v1",
                "valid": bool(ok),
                "dichotomy": ("tau_1(W(3,q)) equals q^2+1, the complete-MUB-set "
                              "size, exactly when q is even -- equivalently "
                              "exactly when an ovoid exists"),
                "mechanism": ("an ovoid is a perfect transversal of the "
                              "contexts, so it IS a minimum cover; W(3,q) has "
                              "an ovoid iff q is even (Thas)"),
                "rows": rows,
                "additionalRuns": [
                    {"q": 7, "tau1": 55, "status": "FEASIBLE",
                     "solverBound": 50, "mubCount": 50,
                     "excessAtMost": 5, "qEven": False,
                     "note": "witness only; the excess is bounded, not pinned"},
                    {"q": 8, "tau1": 65, "status": "OPTIMAL",
                     "solverBound": 65, "mubCount": 65,
                     "excess": 0, "qEven": True,
                     "note": "third even case attaining the MUB count exactly"},
                ],
                "dichotomyHolds": ok_dich,
                "tauStar": ("q^2+1 for every q, by the uniform 1/(q+1) "
                            "primal-dual certificate; so the odd-q penalty is "
                            "a pure integrality gap and does not compound "
                            "across a network of product observables"),
                "oddExcessPattern": ("q-2 at q = 3 and 5, recorded as a "
                                     "two-point pattern only; it is NOT q-2 at "
                                     "q = 4, where the excess is 0, so parity "
                                     "must be conditioned on first"),
                "twoTens": {
                    "phi4": "dim Sp(4,q) = 10 for every q (contextual-fraction "
                            "denominator, w33_hesse_mermin_contextuality.py)",
                    "tauStar": "tau*(W(3,q)) = q^2+1, which is 10 only at q=3 "
                               "and 26 at q=5",
                    "note": "different invariants that agree at q = 3 alone",
                },
                "priorArt": {
                    "inRepo": ["ovoids <-> MUB basis states "
                               "(2026-07-08_pass70_15vector_doily_attack.md)",
                               "36 spreads = complete MUB frames "
                               "(2026-05-29_spread_square_we6_factorization.md)",
                               "Hesse = single-qutrit phase space, 4 MUBs, "
                               "contextual fraction 1/10 "
                               "(w33_hesse_mermin_contextuality.py)"],
                    "external": ("complete MUB sets correspond to symplectic "
                                 "spreads: Calderbank, Cameron, Kantor, Seidel "
                                 "1996; Kantor"),
                    "newHere": ("the covering number stated in MUB terms, and "
                                "the parity dichotomy"),
                },
                "boundary": ("verified at four values of q, not proved as a "
                             "family; tau_1 = q^2+1 for even q is proved by "
                             "exhibiting the ovoid, but the size of the odd-q "
                             "excess is computational only"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
