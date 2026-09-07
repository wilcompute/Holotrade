#!/usr/bin/env python3
"""
The cheap opcodes, the expensive instructions and the spreads are the three
orthogonal-group orbits on the points of a single projective space:
121 = 40 + 45 + 36.

WHAT 424111b LEFT UNEXPLAINED.  It showed the cost graph is a quadrangle only at
q = 3, strongly regular at q = 5, and not even that at q = 7, with exact closed
forms for its size and degree -- q^2(q^2+1)/2 vertices, q(q^2-1)/2 degree -- but
no reason for either the closed forms or the collapse. Both come from one fact.

Sp(4,q) IS O(5,q) FOR ODD q, and under that classical isomorphism the whole
picture is a single projective space cut by a quadratic form:

    |PG(4,q)|      =   isotropic     +      square       +    nonsquare
    (q^5-1)/(q-1)  = (q+1)(q^2+1)    +   q^2(q^2+1)/2    +  q^2(q^2-1)/2

    q = 3    121   =      40         +        45          +       36
    q = 5    781   =     156         +       325          +      300
    q = 7   2801   =     400         +      1225          +     1176

The identity holds exactly at all three. And at q = 3 the three parts are the
three things this whole thread has been about:

    40  isotropic points        = the points of W(3,3)   = the CHEAP opcodes
    45  square nonisotropic     = the EXPENSIVE instructions
    36  nonsquare nonisotropic  = the spread / double-six count

THE MIDDLE ONE IS PROVED, NOT MATCHED.  Building the square-type nonisotropic
points of O(5,3) independently -- from the quadratic form x0^2 + x1x2 + x3x4,
joined by PERPENDICULARITY -- and searching for a graph isomorphism against the
cost anomalies joined by ANTICOMMUTATION:

    side A  cost anomalies                45 vertices, degree 12
    side B  square nonisotropic points    45 vertices, degree 12
    explicit isomorphism found            yes
    bijective, edge-preserving both ways  yes

So the cost anomalies ARE the square-type nonisotropic points, and my
"anticommutes in Sp" is their "perpendicular in O(5,q)" -- which is exactly
right, since anticommuting reflections in Sp become commuting ones in PSp, and
orthogonal reflections commute precisely when their axes are perpendicular.

WHICH EXPLAINS BOTH THINGS 424111b COULD NOT.  The closed forms are just the
orbit sizes of the orthogonal group on PG(4,q). And the collapse is not
mysterious either: this graph is the NO family on nonisotropic points of a polar
space, and those are strongly regular only for small parameters. The cost
geometry was never a quadrangle in general; it is an orbit graph that happens to
be one at q = 3.

WHAT IS ACTUALLY BEING SAID.  Cheap opcode, expensive instruction, and spread
are not three constructions that happen to share a symmetry group. They are the
three classes a quadratic form cuts PG(4,q) into -- isotropic, square,
nonsquare. The machine's fast path, its slow path and its scheduling objects are
one point set, sorted by the value of a single form.

SCOPE.  The counting identity is verified exactly at q = 3, 5, 7 and is a
classical orbit count, cited not proved in general. The isomorphism between the
cost anomalies and the square class is EXPLICIT and verified at q = 3 in both
directions; it is not built at q = 5 or 7, where the parameter and failure-mode
match of 424111b is evidence but not proof. The 40 isotropic points being
W(3,3)'s is the classical content of Sp(4,q) = O(5,q), cited. The 36 nonsquare
points matching the spread count is a COUNT MATCH ONLY -- it is not shown here
that they are the 36 spreads as a PSp-set, and that is the obvious next thing to
build. tau_2 is untouched.
"""

import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def partition(q):
    tot = (q ** 5 - 1) // (q - 1)
    iso = (q + 1) * (q * q + 1)
    sq = q * q * (q * q + 1) // 2
    ns = q * q * (q * q - 1) // 2
    return {"q": q, "pointsOfPG4": tot, "isotropic": iso, "square": sq,
            "nonsquare": ns, "identityHolds": tot == iso + sq + ns}


def cost_graph(q):
    D = 4

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % q

    def nm4(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    pts = sorted({nm4(v) for v in itertools.product(range(q), repeat=D)
                  if any(v)})

    def rk_rows(rows):
        R = [list(x) for x in rows]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, len(R)) if R[i][c] % q), None)
            if p is None:
                continue
            R[r], R[p] = R[p], R[r]
            iv = pow(R[r][c], -1, q)
            R[r] = [(x * iv) % q for x in R[r]]
            for i in range(len(R)):
                if i != r and R[i][c] % q:
                    f = R[i][c]
                    R[i] = [(R[i][j] - f * R[r][j]) % q for j in range(D)]
            r += 1
        return r

    seen, refl = set(), []
    for a, b in itertools.combinations(pts, 2):
        if form(a, b) % q == 0:
            continue
        S = set()
        for x in range(q):
            for y in range(q):
                if x == y == 0:
                    continue
                w = tuple((x * a[k] + y * b[k]) % q for k in range(D))
                if any(w):
                    S.add(nm4(w))
        S = frozenset(S)
        if S in seen:
            continue
        seen.add(S)
        P = [v for v in pts if form(v, a) % q == 0 and form(v, b) % q == 0]
        pb = []
        for v in P:
            if rk_rows(pb + [v]) == len(pb) + 1:
                pb.append(v)
        B = [list(a), list(b)] + [list(x) for x in pb]
        Mb = np.array([[B[j][i] for j in range(D)] for i in range(D)],
                      dtype=np.int64) % q
        Aug = np.concatenate([Mb, np.eye(D, dtype=np.int64)], axis=1)
        r = 0
        for c in range(D):
            p = next(i for i in range(r, D) if Aug[i, c] % q)
            Aug[[r, p]] = Aug[[p, r]]
            Aug[r] = (Aug[r] * pow(int(Aug[r, c]), -1, q)) % q
            for i in range(D):
                if i != r and Aug[i, c] % q:
                    Aug[i] = (Aug[i] - Aug[i, c] * Aug[r]) % q
            r += 1
        Dg = np.diag([q - 1, q - 1, 1, 1]).astype(np.int64)
        refl.append((Mb.dot(Dg).dot(Aug[:, D:] % q)) % q)
    keys = {}
    for Mm in refl:
        a = tuple(Mm.flatten())
        b = tuple(((-Mm) % q).flatten())
        keys[min(a, b)] = True
    C = np.array([np.array(k, dtype=np.int64).reshape(4, 4)
                  for k in sorted(keys)])
    GH = np.einsum('aij,bjk->abik', C, C) % q
    HG = np.transpose(GH, (1, 0, 2, 3))
    A = np.all(GH == ((-HG) % q), axis=(2, 3)).astype(np.int64)
    np.fill_diagonal(A, 0)
    return A


def square_class_graph(q):
    def Qf(x):
        return (x[0] * x[0] + x[1] * x[2] + x[3] * x[4]) % q

    def Bf(x, y):
        return (Qf([(x[i] + y[i]) % q for i in range(5)]) - Qf(x) - Qf(y)) % q

    def nm5(v):
        i = next(k for k, z in enumerate(v) if z % q)
        s = pow(v[i] % q, -1, q)
        return tuple((s * z) % q for z in v)

    p5 = sorted({nm5(v) for v in itertools.product(range(q), repeat=5)
                 if any(v)})
    sqset = {(x * x) % q for x in range(1, q)}
    SQ = [p for p in p5 if Qf(p) % q in sqset]
    m = len(SQ)
    A = np.zeros((m, m), dtype=np.int64)
    for i, j in itertools.combinations(range(m), 2):
        if Bf(SQ[i], SQ[j]) % q == 0:
            A[i, j] = A[j, i] = 1
    return A


def main():
    rows = [partition(q) for q in (3, 5, 7)]

    A1 = cost_graph(3)
    A2 = square_class_graph(3)
    n, m = len(A1), len(A2)
    a1, a2 = A1.tolist(), A2.tolist()
    order, seenv = [0], {0}
    while len(order) < n:
        grew = False
        for v in list(order):
            for u in range(n):
                if a1[v][u] and u not in seenv:
                    seenv.add(u)
                    order.append(u)
                    grew = True
        if not grew:
            for u in range(n):
                if u not in seenv:
                    seenv.add(u)
                    order.append(u)
                    break
    sol = [None]

    def bt(pos, mp, used):
        if sol[0] is not None:
            return
        if pos == n:
            sol[0] = dict(mp)
            return
        v = order[pos]
        for c in range(m):
            if c in used:
                continue
            if all(a1[v][u] == a2[c][mp[u]] for u in order[:pos]):
                mp[v] = c
                used.add(c)
                bt(pos + 1, mp, used)
                del mp[v]
                used.discard(c)
                if sol[0] is not None:
                    return

    bt(0, {}, set())
    phi = sol[0]
    bij = phi is not None and len(set(phi.values())) == n
    edge = bij and all(a1[i][j] == a2[phi[i]][phi[j]]
                       for i in range(n) for j in range(n) if i != j)

    print("THE WHOLE MACHINE IS ONE PROJECTIVE SPACE")
    print("=" * 72)
    print("  Sp(4,q) = O(5,q) for odd q, and PG(4,q) splits by the form:")
    print()
    print("    q   |PG(4,q)|   isotropic   square   nonsquare   identity")
    for r in rows:
        print("   %2d      %5d        %4d     %5d       %5d       %s"
              % (r["q"], r["pointsOfPG4"], r["isotropic"], r["square"],
                 r["nonsquare"], r["identityHolds"]))
    print()
    print("  at q = 3:   121 = 40 + 45 + 36")
    print("     40  isotropic       = the points of W(3,3) = CHEAP opcodes")
    print("     45  square          = the EXPENSIVE instructions")
    print("     36  nonsquare       = the spread / double-six count")
    print()
    print("  side A  cost anomalies (anticommuting)   %d vertices, deg %s"
          % (n, sorted(set(A1.sum(1).tolist()))))
    print("  side B  square nonisotropic (perp)       %d vertices, deg %s"
          % (m, sorted(set(A2.sum(1).tolist()))))
    print("  explicit isomorphism found               %s" % (phi is not None))
    print("  bijective, edge-preserving both ways     %s" % edge)
    print()
    print("  So 'anticommutes in Sp' IS 'perpendicular in O(5,q)' -- right,")
    print("  because anticommuting reflections in Sp commute in PSp, and")
    print("  orthogonal reflections commute exactly when their axes are perp.")
    print()
    print("  THIS EXPLAINS WHAT 424111b COULD NOT: the closed forms are just")
    print("  orthogonal-group ORBIT SIZES on PG(4,q), and the collapse is that")
    print("  this is the NO family on nonisotropic points of a polar space,")
    print("  strongly regular only for small parameters. The cost geometry was")
    print("  never a quadrangle in general -- it is an orbit graph that happens")
    print("  to be one at q = 3.")
    print()
    print("  Cheap opcode, expensive instruction and spread are not three")
    print("  constructions sharing a symmetry group. They are the three classes")
    print("  a quadratic form cuts PG(4,q) into. The fast path, the slow path")
    print("  and the scheduling objects are ONE point set, sorted by one form.")

    ok = (all(r["identityHolds"] for r in rows) and n == 45 and m == 45
          and bij and edge and rows[0]["isotropic"] == 40
          and rows[0]["square"] == 45 and rows[0]["nonsquare"] == 36)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "machine_is_one_projective_space.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.machine-is-one-projective-space.v1",
                "valid": bool(ok),
                "whatWasUnexplained": ("424111b showed the cost graph is a "
                                       "quadrangle only at q = 3 with exact "
                                       "closed forms for size and degree, but "
                                       "gave no reason for either the closed "
                                       "forms or the collapse"),
                "theIdentity": {
                    "formula": ("(q^5-1)/(q-1) = (q+1)(q^2+1) + q^2(q^2+1)/2 + "
                                "q^2(q^2-1)/2"),
                    "rows": rows,
                    "viaClassicalIsomorphism": "Sp(4,q) = O(5,q) for odd q",
                },
                "atQ3": {
                    "total": 121,
                    "isotropic": {"count": 40,
                                  "is": "the points of W(3,3), the CHEAP opcodes",
                                  "status": ("classical content of Sp(4,q) = "
                                             "O(5,q), CITED")},
                    "square": {"count": 45,
                               "is": "the EXPENSIVE instructions",
                               "status": "PROVED here by explicit isomorphism"},
                    "nonsquare": {"count": 36,
                                  "is": "the spread / double-six count",
                                  "status": ("COUNT MATCH ONLY -- not shown to "
                                             "be the 36 spreads as a PSp-set")},
                },
                "isomorphism": {
                    "sideA": "cost anomalies joined by ANTICOMMUTATION",
                    "sideB": ("square-type nonisotropic points of O(5,3) from "
                              "x0^2 + x1x2 + x3x4, joined by PERPENDICULARITY"),
                    "vertices": [n, m],
                    "found": phi is not None,
                    "bijective": bij,
                    "edgePreservingBothWays": edge,
                    "whyTheRelationsCorrespond": ("anticommuting reflections in "
                                                  "Sp become commuting ones in "
                                                  "PSp, and orthogonal "
                                                  "reflections commute exactly "
                                                  "when their axes are "
                                                  "perpendicular"),
                },
                "whatItExplains": ("the closed forms are orthogonal-group ORBIT "
                                   "SIZES on PG(4,q); and the collapse is that "
                                   "this is the NO family on nonisotropic points "
                                   "of a polar space, which is strongly regular "
                                   "only for small parameters. The cost geometry "
                                   "was never a quadrangle in general -- it is "
                                   "an orbit graph that happens to be one at "
                                   "q = 3"),
                "theStatement": ("cheap opcode, expensive instruction and spread "
                                 "are not three constructions that happen to "
                                 "share a symmetry group; they are the three "
                                 "classes a quadratic form cuts PG(4,q) into -- "
                                 "isotropic, square, nonsquare. The machine's "
                                 "fast path, slow path and scheduling objects "
                                 "are ONE point set, sorted by the value of a "
                                 "single form"),
                "boundary": ("the counting identity is verified exactly at "
                             "q = 3, 5, 7 and is a classical orbit count, cited "
                             "not proved in general. The isomorphism is EXPLICIT "
                             "and verified at q = 3 in both directions; it is "
                             "NOT built at q = 5 or 7, where 424111b's parameter "
                             "and failure-mode match is evidence but not proof. "
                             "The 40 isotropic points being W(3,3)'s is the "
                             "classical content of Sp(4,q) = O(5,q), cited. The "
                             "36 nonsquare points matching the spread count is a "
                             "COUNT MATCH ONLY and is the obvious next thing to "
                             "build. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
