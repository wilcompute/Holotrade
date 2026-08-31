#!/usr/bin/env python3
"""
The two dual measurement questions have opposite answers, and the rank-3 case
shows it in one geometry: no ovoid, but a perfect spread.

TWO QUESTIONS ON THE SAME OBJECT.  W(2n-1,q) carries the n-qudit Pauli classes
with commutation, and its maximal totally isotropic subspaces are the maximal
commuting sets -- the measurement CONTEXTS. There are two dual covering
questions, and both are operational:

  COVER THE CONTEXTS WITH OBSERVABLES (tau_1). The fewest Paulis such that
  every context contains one. This is certification: no stabilizer hides from
  your measurement set. The optimum is q^n+1 exactly when an OVOID exists.

  COVER THE OBSERVABLES WITH CONTEXTS. The fewest contexts such that every
  Pauli lies in one. This is the Pauli-GROUPING problem practitioners solve to
  cut measurement rounds -- one measurement setting per commuting group. The
  optimum is q^n+1 exactly when a SPREAD exists.

Ovoids and spreads are dual objects, so there is no reason for the two to
agree. They do not, and the gap is total.

THE ANSWERS.

  perfect_context_transversal_classification.py, via Thas: an ovoid exists iff
  n = 2 AND q is even. So certification is free for two qudits of even
  dimension and for nothing else -- not for any odd dimension, and not for
  three or more carriers at any dimension.

  Here: the minimum context cover is q^n+1 in EVERY case tested, always
  OPTIMAL, and always attained by an exact PARTITION rather than an
  overlapping cover -- a spread. Symplectic polar spaces have spreads for all
  n and q, so grouping is always free.

    system      space     min context cover   q^n+1   partition?
    2 qubits    W(3,2)            5             5        yes
    2 qutrits   W(3,3)           10            10        yes
    2 ququarts  W(3,4)           17            17        yes
    2 ququints  W(3,5)           26            26        yes
    3 qubits    W(5,2)            9             9        yes

THE RANK-3 ROW IS THE WHOLE POINT.  W(5,2) is one geometry answering both
questions at once:

    covering contexts with observables:  tau_1 = 10 > 9   -- NOT free
    covering observables with contexts:  cover  =  9 = 9   -- free, exact
                                                              partition

No ovoid, but a perfect spread. Three qubits can always be grouped into nine
commuting measurement settings with no observable measured twice, yet cannot
be certified by nine observables -- ten are needed.

SO THE ASYMMETRY IS THE RESULT.  Grouping is always optimally solvable at the
MUB count, at every dimension and every number of carriers. Certification is
optimally solvable only in the single case of two even-dimensional qudits.
Practitioners who reduce measurement rounds are working on the easy side of a
duality whose other side is almost always obstructed.

PRIOR ART.  For qubits the grouping statement is classical: the 4^n - 1
non-identity Paulis partition into 2^n + 1 commuting sets, which is the
standard MUB/symplectic-spread construction (Calderbank, Cameron, Kantor and
Seidel). This repository has carried spreads as MUB frames since May. What is
added is the pairing -- reading grouping and certification as the two dual
covering problems on one space, and the observation that they dualize to
opposite answers, sharpest at rank 3 where a single geometry gives both.

SCOPE.  Each row is a solved instance. The universality of spreads is a
classical fact, not something these five rows prove; they exist to check that
the dual is stated correctly and to exhibit the rank-3 contrast. No tau_2
bound moves.
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
    raise ValueError(q)


def build(n, q):
    els, add, mul = gf(q)
    inv = {a: next(b for b in els if mul[a][b] == 1) for a in els if a}
    dim = 2 * n

    def nm(v):
        i = next(k for k, x in enumerate(v) if x != 0)
        return tuple(mul[inv[v[i]]][x] for x in v)

    def form(u, v):
        acc = 0
        for i in range(n):
            a, b = mul[u[2 * i]][v[2 * i + 1]], mul[u[2 * i + 1]][v[2 * i]]
            acc = (acc ^ a ^ b) if q % 2 == 0 else (acc + a - b)
        return acc if q % 2 == 0 else acc % q

    pts = sorted({nm(v) for v in itertools.product(els, repeat=dim) if any(v)})
    idx = {p: i for i, p in enumerate(pts)}
    N = len(pts)

    def span(basis):
        S = set()
        for cs in itertools.product(els, repeat=len(basis)):
            if not any(cs):
                continue
            w = [0] * dim
            for c, bb in zip(cs, basis):
                for k in range(dim):
                    w[k] = add[w[k]][mul[c][bb[k]]]
            if any(w):
                S.add(idx[nm(tuple(w))])
        return frozenset(S)

    target = (q ** n - 1) // (q - 1)
    ctx, seen = set(), set()

    def ext(basis, cur):
        if len(cur) == target:
            ctx.add(cur)
            return
        if cur in seen:
            return
        seen.add(cur)
        for p in range(N):
            if p in cur:
                continue
            if all(form(pts[p], pts[c]) == 0 for c in cur):
                ext(basis + [pts[p]], span(basis + [pts[p]]))

    for p in range(N):
        ext([pts[p]], span([pts[p]]))
    return N, sorted(ctx)


def main():
    print("THE DUAL MEASUREMENT QUESTION NEVER FAILS")
    print("=" * 72)
    print("  Covering CONTEXTS with observables (certification) is free only")
    print("  for two qudits of even dimension -- Thas. Covering OBSERVABLES")
    print("  with contexts (Pauli grouping) needs a SPREAD, and those always")
    print("  exist. Ovoids and spreads are dual, so the two need not agree.")
    print()
    rows = []
    for label, n, q, budget in (("2 qubits", 2, 2, 60.0),
                                ("2 qutrits", 2, 3, 180.0),
                                ("2 ququarts", 2, 4, 600.0),
                                ("2 ququints", 2, 5, 1200.0),
                                ("3 qubits", 3, 2, 600.0)):
        N, ctx = build(n, q)
        m = cp_model.CpModel()
        y = [m.NewBoolVar("") for _ in ctx]
        for p in range(N):
            m.AddBoolOr([y[i] for i, C in enumerate(ctx) if p in C])
        m.Minimize(sum(y))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = budget
        s.parameters.num_search_workers = 8
        st = s.Solve(m)
        cov = int(s.ObjectiveValue())
        chosen = [ctx[i] for i in range(len(ctx)) if s.Value(y[i])]
        covered = set().union(*chosen) if chosen else set()
        is_partition = (len(covered) == N
                        and sum(len(C) for C in chosen) == N)
        rows.append({
            "system": label, "space": "W(%d,%d)" % (2 * n - 1, q),
            "n": n, "q": q, "pauliClasses": N, "contexts": len(ctx),
            "contextSize": len(ctx[0]),
            "minContextCover": cov, "status": s.StatusName(st),
            "spreadValue": q ** n + 1, "excess": cov - (q ** n + 1),
            "isExactPartition": bool(is_partition),
        })
        print("  %-11s %-8s cover = %-3d (%s) | q^n+1 = %-3d | excess %d | "
              "exact partition: %s"
              % (label, rows[-1]["space"], cov, s.StatusName(st),
                 q ** n + 1, cov - (q ** n + 1), is_partition))
    print()
    allfree = all(r["excess"] == 0 and r["isExactPartition"] for r in rows)
    print("  every case free, and every optimum an exact partition: %s"
          % allfree)
    print()
    print("  THE RANK-3 ROW answers both questions in ONE geometry:")
    print("     W(5,2), covering contexts with observables: tau_1 = 10 > 9")
    print("     W(5,2), covering observables with contexts: cover = 9 = 9")
    print("  No ovoid, but a perfect spread. Three qubits group into nine")
    print("  commuting settings with nothing measured twice, yet cannot be")
    print("  certified by nine observables -- ten are needed.")

    ok = allfree
    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data",
                         "the_dual_measurement_question_never_fails.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.dual-measurement-question.v1",
                "valid": bool(ok),
                "twoQuestions": {
                    "certification": ("cover every CONTEXT with observables; "
                                      "optimum q^n+1 iff an ovoid exists, "
                                      "which by Thas means n = 2 and q even"),
                    "grouping": ("cover every OBSERVABLE with contexts, the "
                                 "Pauli-grouping problem; optimum q^n+1 iff a "
                                 "spread exists, and spreads always do"),
                },
                "rows": rows,
                "groupingAlwaysFree": allfree,
                "rank3Contrast": {
                    "space": "W(5,2)",
                    "certification": {"tau1": 10, "value": 9, "free": False},
                    "grouping": {"cover": 9, "value": 9, "free": True,
                                 "exactPartition": True},
                    "reading": ("three qubits group into nine commuting "
                                "settings with nothing measured twice, yet "
                                "cannot be certified by nine observables"),
                },
                "priorArt": ("for qubits the grouping statement is classical: "
                             "the 4^n-1 Paulis partition into 2^n+1 commuting "
                             "sets, the standard MUB/symplectic-spread "
                             "construction; this repository has carried "
                             "spreads as MUB frames since May 2026"),
                "whatIsAdded": ("the pairing -- reading grouping and "
                                "certification as the two dual covering "
                                "problems on one space, and the observation "
                                "that they dualize to opposite answers, "
                                "sharpest at rank 3"),
                "boundary": ("each row is a solved instance; the universality "
                             "of spreads is classical and not proved by these "
                             "five rows. No tau_2 bound moves."),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
