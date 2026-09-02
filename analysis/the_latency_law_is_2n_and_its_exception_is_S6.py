#!/usr/bin/env python3
"""
The architecture's worst-case program length is 2n -- logarithmic in the state
count -- with exactly one exception, and the exception is S6 again.

WHERE THIS COMES FROM.  b363f7c measured the full transvection ISA on Sp(4,3)
and got Cayley diameter 4. For Sp(2n,q) with n = 2 that is 2n, which smells
like a law rather than a number, and the symplectic analogue of
Cartan-Dieudonne says every element IS a product of transvections. So: is the
diameter always 2n? A law with no exceptions on one sample is not a law, so run
several (n, q).

    n  q   2n   points   transvections    |G|        diameter   = 2n?
    1  2    2        3          3            6           2       yes
    1  3    2        4          8           12           2       yes
    1  5    2        6         24           60           2       yes
    1  7    2        8         48          168           2       yes
    2  2    4       15         15          720           5       NO
    2  3    4       40         80       25,920           4       yes
    3  2    6       63         63    1,451,520           6       yes

Six of seven land exactly on 2n. The one that does not is Sp(4,2), whose
diameter is 5 = 2n + 1.

AND THE EXCEPTION IS S6.  Sp(4,2) is isomorphic to S6 -- the unique symmetric
group with an exceptional outer automorphism, and the same group whose outer
automorphism drives the carrier fork of fed190d, where the two 216-state
carriers turned out to be exchanged by out(S6) and by nothing inside the
substrate. The one place the latency law breaks is the one place the symmetry
story is exceptional too.

It is not a characteristic-two effect. Sp(6,2) has 63 transvections and
diameter exactly 6 = 2n, and Sp(2,2) = S3 has diameter 2. The exception is
specifically (n, q) = (2, 2).

A FOURTH ARRIVAL AT THE SAME ASYMMETRY.  W33-Theory's PASS4714 is titled
"three tracks reached the point/line asymmetry independently, by three
methods" -- signing densities, association schemes, and non-backtracking walk
masses -- and its explanation is exactly the fact behind this exception:

    GQ(2,2) is W(3,2), and q = 2 is even, so it is precisely the SELF-DUAL
    member. Track C's exceptional cancellation is not a coincidence; it is the
    one quadrangle whose two carriers are the same object, so a quantity
    computed on points and one computed on lines must agree.

Sp(4,2) IS that quadrangle. The 15 points are the doily, GQ(2,2) = W(3,2), and
the diameter law breaks there for the same structural reason the other three
tracks broke there. This is a fourth arrival at one asymmetry, by a fourth
method -- Cayley diameter -- and it was not looked for.

AND IT IS THE SAME SPLIT THIS WHOLE THREAD RUNS ON.  Four separate results here
turn on the identical q = 2 versus q = 3 distinction:

    tau_2 != 110          needs W(q) self-dual ONLY for even q; the endgame
                          works at q = 3 and would fail at q = 2
    composition tax       zero at q = 2, where ovoids exist and W(3,2)^2 = 25
                          = tau_1^2 exactly; nonzero at q = 3
    carrier fork          non-gauge, driven by out(S6) = out(Sp(4,2))
    latency law           2n at q = 3, 2n + 1 at q = 2

PASS4714 named the split and gave three arrivals; the diameter is a fourth, and
the fork and the tax are two more. The doily is not a small case of W(3,3) --
it is the place every argument in this thread changes sign.

THE SCALING LAW, which is the architectural point.  The carrier has
(q^(2n) - 1)/(q - 1) states, so the state count grows like q^(2n) while the
worst-case program grows like 2n:

    worst-case program length  =  2n  =  O(log_q |states|).

Universality at logarithmic depth. Doubling the rank doubles the program and
squares the state space. Our machine is Sp(4,3), which sits ON the law at
diameter 4, not on the exception.

WHERE THE LITERATURE SITS.  The symplectic Cartan-Dieudonne theorem gives that
every element of a symplectic group is a product of transvections, and work on
factorisation length relates it to the residue dimension dim im(g - 1). The
exact maximum length for the specific groups here does not appear in the
accessible literature, so these diameters are computed rather than quoted -- and
the Sp(4,2) exception is the kind of thing a general bound would hide.

SCOPE.  Seven cases, each an exact full BFS over the whole group with the
complete transvection set. That is evidence for the 2n law and an exact
counterexample at (2,2); it is not a proof of the law in general, and no claim
is made about larger n or about non-transvection generating sets. The
identification Sp(4,2) = S6 is classical. tau_2 is untouched.
"""

import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"


def run(n, q, cap=4_000_000):
    d = 2 * n

    def nm(v):
        i = next(k for k, x in enumerate(v) if x % q)
        z = pow(v[i] % q, -1, q)
        return tuple((z * x) % q for x in v)

    def form(u, v):
        s = 0
        for i in range(n):
            s += u[i] * v[n + i] - u[n + i] * v[i]
        return s % q

    pts = sorted({nm(v) for v in itertools.product(range(q), repeat=d)
                  if any(v)})
    idx = {v: i for i, v in enumerate(pts)}
    N = len(pts)
    ident = tuple(range(N))
    T = set()
    for p in range(N):
        vv = pts[p]
        for lam in range(1, q):
            out = []
            for r in range(N):
                x = pts[r]
                c = (lam * form(x, vv)) % q
                out.append(idx[nm(tuple((x[k] + c * vv[k]) % q
                                        for k in range(d)))])
            t = tuple(out)
            if t != ident:
                T.add(t)
    T = sorted(T)
    dist, fr, dia = {ident: 0}, [ident], 0
    while fr:
        nx = []
        for a in fr:
            for g in T:
                c = tuple(a[g[i]] for i in range(N))
                if c not in dist:
                    dist[c] = dia + 1
                    nx.append(c)
                    if len(dist) > cap:
                        return None
        fr = nx
        if nx:
            dia += 1
    return {"n": n, "q": q, "twoN": d, "points": N,
            "transvections": len(T), "groupOrder": len(dist),
            "diameter": dia, "equalsTwoN": dia == d}


def main():
    cases = [(1, 2), (1, 3), (1, 5), (1, 7), (2, 2), (2, 3), (3, 2)]
    rows = []
    print("THE LATENCY LAW IS 2n, AND ITS EXCEPTION IS S6")
    print("=" * 72)
    print("   n  q   2n   points   transvections       |G|   diameter   = 2n?")
    for (n, q) in cases:
        r = run(n, q)
        if r is None:
            print("   %d  %d   %2d   -- too large --" % (n, q, 2 * n))
            continue
        rows.append(r)
        print("   %d  %d   %2d   %6d   %13d %9d   %5d      %s"
              % (r["n"], r["q"], r["twoN"], r["points"], r["transvections"],
                 r["groupOrder"], r["diameter"], r["equalsTwoN"]))
    exc = [r for r in rows if not r["equalsTwoN"]]
    print()
    print("  on the law: %d of %d" % (len(rows) - len(exc), len(rows)))
    for r in exc:
        print("  EXCEPTION: Sp(%d,%d), diameter %d = 2n + %d"
              % (r["twoN"], r["q"], r["diameter"], r["diameter"] - r["twoN"]))
    print()
    print("  Sp(4,2) is S6 -- the unique symmetric group with an exceptional")
    print("  outer automorphism, and the same group whose out(S6) drives the")
    print("  carrier fork of fed190d. The one place the latency law breaks is")
    print("  the one place the symmetry story is exceptional too.")
    print()
    print("  Not a characteristic-two effect: Sp(6,2) has diameter exactly 6")
    print("  and Sp(2,2) exactly 2. The exception is specifically (n,q)=(2,2).")
    print()
    print("  SCALING: the carrier has (q^2n - 1)/(q - 1) states while the")
    print("  worst-case program is 2n, so program length = O(log_q |states|).")
    print("  Universality at logarithmic depth. Our machine is Sp(4,3), which")
    print("  sits ON the law at diameter 4, not on the exception.")

    ok = (len(rows) == 7 and len(exc) == 1 and exc[0]["n"] == 2
          and exc[0]["q"] == 2 and exc[0]["diameter"] == 5
          and any(r["n"] == 2 and r["q"] == 3 and r["diameter"] == 4
                  for r in rows)
          and any(r["n"] == 3 and r["q"] == 2 and r["diameter"] == 6
                  for r in rows))

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_latency_law_is_2n.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.transvection-latency-law-2n.v1",
                "valid": bool(ok),
                "question": ("b363f7c got Cayley diameter 4 for Sp(4,3) with "
                             "the full transvection ISA, and 2n = 4; the "
                             "symplectic Cartan-Dieudonne theorem says every "
                             "element IS a product of transvections, so is the "
                             "diameter always 2n?"),
                "cases": rows,
                "onTheLaw": len(rows) - len(exc),
                "tested": len(rows),
                "exception": {
                    "group": "Sp(4,2)",
                    "n": 2, "q": 2,
                    "diameter": exc[0]["diameter"] if exc else None,
                    "excess": (exc[0]["diameter"] - exc[0]["twoN"]) if exc else None,
                    "isS6": True,
                    "whyItMatters": ("Sp(4,2) = S6, the unique symmetric group "
                                     "with an exceptional outer automorphism, "
                                     "and the same group whose out(S6) drives "
                                     "the carrier fork of fed190d -- the one "
                                     "place the latency law breaks is the one "
                                     "place the symmetry story is exceptional"),
                    "notCharacteristicTwo": ("Sp(6,2) has diameter exactly 6 "
                                             "and Sp(2,2) exactly 2, so the "
                                             "exception is specifically (2,2)"),
                },
                "scalingLaw": {
                    "states": "(q^(2n) - 1)/(q - 1)",
                    "worstCaseProgram": "2n",
                    "reading": ("program length = O(log_q |states|), i.e. "
                                "universality at logarithmic depth: doubling "
                                "the rank doubles the program and squares the "
                                "state space"),
                    "ourMachine": ("Sp(4,3) sits ON the law at diameter 4, not "
                                   "on the exception"),
                },
                "fourthArrival": {
                    "priorArt": ("W33-Theory PASS4714, 'three tracks reached "
                                 "the point/line asymmetry independently': "
                                 "signing densities, association schemes, and "
                                 "non-backtracking walk masses"),
                    "theirExplanation": ("GQ(2,2) is W(3,2) and q = 2 is even, "
                                         "so it is precisely the SELF-DUAL "
                                         "member -- the one quadrangle whose "
                                         "two carriers are the same object"),
                    "thisIsTheFourth": ("Sp(4,2) is that quadrangle; the 15 "
                                        "points are the doily, and the diameter "
                                        "law breaks there for the same "
                                        "structural reason. A fourth arrival by "
                                        "a fourth method, not looked for"),
                    "sameSplitFourWays": [
                        "tau_2 != 110 needs W(q) self-dual only for even q",
                        "composition tax zero at q=2 where ovoids exist "
                        "(W(3,2)^2 = 25 = tau_1^2), nonzero at q=3",
                        "the carrier fork is non-gauge, driven by "
                        "out(S6) = out(Sp(4,2))",
                        "the latency law is 2n at q=3 and 2n+1 at q=2",
                    ],
                    "reading": ("the doily is not a small case of W(3,3) -- it "
                                "is the place every argument in this thread "
                                "changes sign"),
                },
                "literature": ("the symplectic Cartan-Dieudonne theorem gives "
                               "that every element is a product of "
                               "transvections, and factorisation-length work "
                               "relates length to the residue dimension "
                               "dim im(g-1); the exact maximum length for these "
                               "specific groups is not in the accessible "
                               "literature, so these diameters are computed "
                               "rather than quoted, and the Sp(4,2) exception "
                               "is the kind of thing a general bound hides"),
                "boundary": ("seven cases, each an exact full BFS over the whole "
                             "group with the complete transvection set; that is "
                             "evidence for the 2n law and an exact "
                             "counterexample at (2,2), not a proof of the law "
                             "in general. No claim about larger n or about "
                             "non-transvection generating sets. Sp(4,2) = S6 is "
                             "classical. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
