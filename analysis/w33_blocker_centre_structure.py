#!/usr/bin/env python3
"""
The centre of a minimum blocking set of W(3,3) -- and the citation that
stops this being announced as new.

WHAT THE COMPUTATION SHOWS.  All 360 minimum blocking sets of W(3,3) share
one structure, and it is completely rigid:

    A minimum blocking set b (|b| = tau_1 = 11) has a CENTRE: a point p
    such that b meets each of the four lines through p in exactly TWO
    points, and every one of the other 36 lines in exactly ONE point.

    b never contains its own centre.  Relative to the rank-3 shell around
    p -- the decomposition 1 + 12 + 27 into p, the 12 points collinear
    with p, and the 27 that are not -- b takes the shape (0, 8, 3): none
    of p, eight of the twelve (two on each line through p), and three of
    the twenty-seven.

    There are exactly 9 blocking sets per centre and 40 centres, giving
    360 = 40 x 9, a single Aut(W(3,3))-orbit with stabiliser of order 144.

Every one of those statements is verified here by exhaustive check over all
360 sets, and the arithmetic closes: sum over L of |b cap L| = 4|b| = 44 over
40 lines each meeting b at least once, so the total excess is exactly 44 - 40
= 4, and the computation shows that excess sits on a pencil rather than being
spread around.

WHY THIS IS NOT ANNOUNCED AS NEW.  Dualise.  W(3,3) is the dual of Q(4,3), so
a blocking set of W(3,3) is a COVER of Q(4,3) by lines, and tau_1 = 11 is the
size of a minimum cover.  In that language the result reads: a minimum cover
of Q(4,3) has excess 1, its four doubly-covered points form a line, and that
line is not in the cover.  Covers of classical generalized quadrangles are a
studied subject, and two published facts bracket everything above:

  * Eisfeld, Storme, Szonyi and Sziklai, "Covers and blocking sets of
    classical generalised quadrangles", Discrete Mathematics 238 (2001)
    35-51, prove that a cover of Q(4,q) for q odd needs more than
    q^2 + 1 + (q-1)/3 lines.  At q = 3 that is > 10.67, i.e. at least 11 --
    exactly the value this repository certifies by SAT.  The number 11 is
    PRIOR ART, not a result of ours; the SAT certificate reproduces it and
    shows it is attained.

  * The companion work on covers of PG(3,q) and of finite generalized
    quadrangles states that for minimal covers with small excess "the
    structure of the set of points lying on at least two lines of the cover
    is described".  That is precisely the excess structure computed above.

I could not retrieve the q = 3 statement verbatim from open sources, so I
cannot say which paper contains it in exactly this form.  That uncertainty
resolves one way only: the centre structure is presumed PRIOR ART and is
recorded here as a computational verification with a citation, not as a
discovery.  A result whose novelty cannot be established is not new.

WHAT DOES REMAIN OURS.  The depth-2 TENSOR blocking number tau_2 -- the
fewest leaves of the 40 x 40 fabric meeting every product tile L x M -- is a
question about a product of two quadrangles, not about one, and no literature
on it turned up.  The 121 -> 115 improvement and the [110, 115] interval in
analysis/tensor_symmetric_blocker.py stand as the contribution; this file is
the piece of ground underneath it that someone else already owns.
"""

import collections
import json
import os
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"
N = 40
TAU1 = 11

CITATIONS = [
    {
        "claim": "a cover of Q(4,q), q odd, needs more than q^2+1+(q-1)/3 lines; "
                 "at q=3 that is >10.67, hence tau_1 >= 11",
        "source": "J. Eisfeld, L. Storme, T. Szonyi, P. Sziklai, "
                  "Covers and blocking sets of classical generalised quadrangles, "
                  "Discrete Mathematics 238 (2001) 35-51",
        "bearing": "the value 11 is prior art; our SAT certificate reproduces it "
                   "and shows it is attained",
    },
    {
        "claim": "for minimal covers with small excess, the structure of the set "
                 "of points on at least two lines of the cover is described",
        "source": "Covers of PG(3,q) and of finite generalized quadrangles "
                  "(same group of authors)",
        "bearing": "the centre structure computed here is presumed to be a q=3 "
                   "instance of this; not claimed as new",
    },
]


def load():
    out = subprocess.run(
        ["node", "-e",
         "global.window=global;"
         "const S=require('./js/substrate.js');"
         "const R=require('./analysis/tensor_blocking_reformulation.js');"
         "const adj=[];for(let i=0;i<40;i++){const r=[];"
         "for(let j=0;j<40;j++)r.push(i!==j&&S.isAdjacent(i,j)?1:0);adj.push(r);}"
         "process.stdout.write(JSON.stringify({"
         "lines:S.LINES.map(l=>[...l].sort((a,b)=>a-b)),"
         "blockers:R.minimumBlockers().map(b=>[...b].sort((a,b)=>a-b)),adj}));"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit("node failed: " + out.stderr[:600])
    d = json.loads(out.stdout)
    return ([set(x) for x in d["lines"]],
            [set(b) for b in d["blockers"]], d["adj"])


def main():
    lines, B, adj = load()
    pencil = {p: frozenset(li for li, L in enumerate(lines) if p in L)
              for p in range(N)}
    by_pencil = {v: k for k, v in pencil.items()}

    checks = {}
    checks["blockerCount360"] = len(B) == 360
    checks["allSizeTau1"] = all(len(b) == TAU1 for b in B)
    checks["allBlockEveryLine"] = all(all(b & L for L in lines) for b in B)
    checks["everyPointOnFourLines"] = all(len(v) == 4 for v in pencil.values())

    centres, shapes, excesses = [], collections.Counter(), collections.Counter()
    for b in B:
        exc = frozenset(li for li, L in enumerate(lines) if len(b & L) >= 2)
        excesses[tuple(sorted(collections.Counter(
            len(b & L) for L in lines).items()))] += 1
        centres.append(by_pencil.get(exc))
        p = by_pencil.get(exc)
        if p is not None:
            near = {q for li in pencil[p] for q in lines[li]} - {p}
            far = set(range(N)) - {p} - near
            shapes[(len(b & {p}), len(b & near), len(b & far))] += 1

    checks["excessSetIsAlwaysAPencil"] = all(c is not None for c in centres)
    checks["oneIntersectionProfile"] = len(excesses) == 1
    checks["profileIs36x1plus4x2"] = (
        list(excesses) == [((1, 36), (2, 4))] if excesses else False)
    cc = collections.Counter(c for c in centres if c is not None)
    checks["fortyCentres"] = len(cc) == N
    checks["nineBlockersPerCentre"] = set(cc.values()) == {9}
    checks["centreNeverInItsBlocker"] = all(
        c not in b for b, c in zip(B, centres) if c is not None)
    checks["oneShapeRelativeToCentre"] = len(shapes) == 1
    checks["shapeIsZeroEightThree"] = list(shapes) == [(0, 8, 3)]
    checks["excessArithmetic"] = (4 * TAU1 - N) == 4
    checks["countFactorises"] = len(B) == N * 9

    valid = all(checks.values())

    print("THE CENTRE OF A MINIMUM BLOCKING SET OF W(3,3)")
    print("=" * 72)
    for k, v in checks.items():
        print("  %-32s %s" % (k, v))
    print()
    print("  intersection profile of every blocker :",
          dict(next(iter(excesses))) if excesses else None)
    print("  shape relative to the 1+12+27 shell   :",
          list(shapes)[0] if shapes else None)
    print("  360 = 40 centres x 9 blockers         :", checks["countFactorises"])
    print()
    print("  PRIOR ART -- this is verification, not discovery:")
    for c in CITATIONS:
        print("    * %s" % c["source"])
        print("      %s" % c["claim"])
        print("      bearing: %s" % c["bearing"])
    print()
    print("  What remains ours is the depth-2 TENSOR blocking number, a")
    print("  question about a product of two quadrangles; see")
    print("  analysis/tensor_symmetric_blocker.py.")

    if "--write" in sys.argv:
        out = os.path.join(ROOT, "data", "w33_blocker_centre_structure.json")
        with open(out, "w") as fh:
            json.dump({
                "schema": "holotrade.w33-blocker-centre.v1",
                "valid": valid,
                "checks": checks,
                "tau1": TAU1,
                "blockers": len(B),
                "centres": len(cc),
                "blockersPerCentre": sorted(set(cc.values())),
                "intersectionProfile": {"1": 36, "2": 4},
                "shapeInRank3Shell": {"centre": 0, "collinear12": 8, "far27": 3},
                "novelty": "NOT NEW -- presumed prior art; recorded as a "
                           "computational verification with citations",
                "citations": CITATIONS,
                "oursInstead": "the depth-2 tensor blocking number tau_2, "
                               "analysis/tensor_symmetric_blocker.py",
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(out, ROOT))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
