#!/usr/bin/env python3
"""
The O(5,q) orbit census this session has been computing IS the weight enumerator
of a published code -- the rank-2 Lagrangian Grassmann code -- and the corpus
should have been citing it. What is ours is the one-line geometric derivation.

THE FIND.  ae04deb reported an exhaustive orbit census over ker(omega):

    q = 3   isotropic 80, hyperbolic 90, elliptic 72   (as VECTORS)
    q = 5             624           1300          1200
    q = 7            2400           7350          7056

Build instead the projective code whose generator matrix has the points of the
parabolic quadric Q(4,q) as its columns -- equivalently, the Pluecker images of
the lines of W(3,q). Its weight distribution, computed exhaustively over all
q^5 codewords, is

    q = 3   [40, 5, 24]     A_24 = 90, A_27 = 80, A_30 = 72
    q = 5   [156, 5, 120]   A_120 = 1300, A_125 = 624, A_130 = 1200
    q = 7   [400, 5, 336]   A_336 = 7350, A_343 = 2400, A_350 = 7056

The census and the weight enumerator are the same numbers. They had to be: a
codeword is a linear functional on W, its weight is N - |H cap Q| for the
corresponding hyperplane H, and by the polarity H = p^perp, so the weight
depends only on the ORBIT of p. Three orbits, three weights, multiplicity
(q-1) times the orbit size.

AND THE CODE IS PUBLISHED.  Cardinali and Giuzzi, "Minimum distance of
Symplectic Grassmann codes" (arXiv:1503.05456; Linear Algebra Appl. 488 (2016)
124-134), introduce exactly this family. Their Main Theorem gives

    N = prod_{i=0}^{k-1} (q^{2n-2i} - 1)/(q^{i+1} - 1),
    K = C(2n,k) - C(2n,k-2),
    and for k = 2 the minimum distance is q^{4n-5} - q^{2n-3}.

At n = k = 2 that is N = (q^4-1)/(q-1) = q^3+q^2+q+1, K = 2n^2-n-1 = 5, and
d = q^3 - q: exactly 40/5/24, 156/5/120, 400/5/336. Since k = n = 2 this is
simultaneously a line Symplectic Grassmann code and the Lagrangian-Grassmannian
code of rank 2, and their abstract states they "provide the full weight
enumerator for the Lagrangian-Grassmannian codes of rank 2 and 3". So the weight
enumerator computed here is THEIRS. No novelty is claimed for the code, its
parameters, or its weight distribution.

THIS IS FAILURE MODE FIVE, CAUGHT BEFORE THE CLAIM.  CLAUDE.md's most expensive
failure mode is rediscovery: correct mathematics, sound witnesses, proportionate
framing, and false novelty. Every number in the census is right and none of it
is new. It is recorded here so the corpus carries the citation rather than the
coincidence.

WHAT IS ACTUALLY OURS, AND IT IS SMALL BUT REAL.  The session's polar-incidence
work gives their minimum distance a one-line geometric derivation. The three
hyperplane sections of Q(4,q) are the tangent cone, the hyperbolic section and
the elliptic section, of sizes

    q^2+q+1,        (q+1)^2,        q^2+1

and (q+1)^2 is the largest for every q > 0, so

    d = N - (q+1)^2 = (q^3+q^2+q+1) - (q^2+2q+1) = q^3 - q

which is their q^{4n-5} - q^{2n-3} at n = 2. The maximum-section hyperplanes are
exactly the 45/325/1225 points of the hyperbolic orbit, so THE MINIMUM-WEIGHT
CODEWORDS ARE THE OCTET SECTIONS OF c9e6be7 -- the same objects that carry the
K(q+1,q+1) grids, the 2(q+1) thick points, and (at q = 3 only) the (c,m)
minimum-blocker labels of aa42b38. The corpus's octets are the minimum-weight
supports of a known code.

THE OTHER HALF: THIS IS THE KLEIN CORRESPONDENCE, AND ITS PHYSICS IS TWISTORS.
Lambda^2(F^4) with the Pfaffian is the Klein correspondence: lines of PG(3,q)
<-> points of the Klein quadric Q+(5,q). Fixing the alternating form omega
selects the hyperplane ker(omega), and Q(4,q) = Q+(5,q) cap ker(omega), whose
points are exactly the totally isotropic lines -- that is, W(3,q). So the whole
apparatus is the Klein correspondence with one bivector fixed.

In Penrose's twistor programme the same diagram carries physics: twistor space
is PG(3,C), its lines are the points of compactified complexified Minkowski
space, and that space IS the Klein quadric. The distinguished bivector is the
INFINITY TWISTOR, and choosing it is exactly what breaks the conformal group
down to Poincare. The dictionary is then

    twistor space PG(3,C)          <->  PG(3,q)
    compactified Minkowski space   <->  Klein quadric Q+(5,q)
    infinity twistor               <->  omega
    conformal -> Poincare          <->  Q+(5,q) -> Q(4,q), i.e. Sp(4,q) = O(5,q)

This is stated as a STRUCTURAL ANALOGY, not a physical claim: no metric, no
signature, no real form, and nothing here about field equations. What it does
say is where the corpus's five-space came from.

AND IT CLOSES THE RANK STORY.  The Klein correspondence exists because the
Pfaffian on Lambda^2(F^4) has degree 2, which is the same fact ae04deb isolated
as the reason the polar apparatus is rank-two only, and c6d1077 continued as the
reason rank 3 is a cubic Jordan algebra instead. Twistor theory's attachment to
four dimensions and this corpus's rank ceiling are one statement: Gr(2,4) is a
quadric and Gr(2,6) is not.

SCOPE.  q = 3, 5, 7, exhaustive over all q^5 codewords, so the weight
distributions are enumerations rather than samples. The identification with
Cardinali-Giuzzi is by their Main Theorem's N, K and d, which are quoted from
the paper and matched against the computation; their weight-enumerator section
is cited from the abstract's statement rather than transcribed, so "the
enumerator is theirs" is an attribution made on the strength of the matching
parameters and the abstract, not a line-by-line comparison. Three weights is a
consequence of three orbits and is not by itself evidence of anything new. The
twistor dictionary is an analogy of structures, with no claim about physics. q
even is excluded throughout: there the symplectic and orthogonal pictures differ
and K is 6, not 5. Nothing here touches tau_2.
"""

import collections
import itertools
import json
import os
import sys

import numpy as np

ROOT = r"C:\Repos\Holotrade"


def study(q):
    rows = []
    for i in range(5):
        for m in range(q ** (4 - i)):
            v = [0] * i + [1]
            x = m
            for _ in range(4 - i):
                v.append(x % q)
                x //= q
            rows.append(v)
    P = np.array(rows, dtype=np.int64)
    Qv = (P[:, 0] * P[:, 1] + P[:, 2] * P[:, 3] + P[:, 4] ** 2) % q
    G = P[Qv == 0].T
    n = int(G.shape[1])

    wd = collections.Counter()
    for co in itertools.product(range(q), repeat=5):
        if not any(co):
            continue
        c = (np.array(co, dtype=np.int64) @ G) % q
        wd[int(np.count_nonzero(c))] += 1

    tangent, hyp, ell = q * q + q + 1, (q + 1) ** 2, q * q + 1
    orbT = (q + 1) * (q * q + 1)
    orbH = q * q * (q * q + 1) // 2
    orbE = q * q * (q * q - 1) // 2
    predicted = {n - tangent: (q - 1) * orbT,
                 n - hyp: (q - 1) * orbH,
                 n - ell: (q - 1) * orbE}

    return {
        "q": q, "N": n, "K": 5,
        "weightDistribution": {str(k): v for k, v in sorted(wd.items())},
        "predictedFromOrbits": {str(k): v for k, v in sorted(predicted.items())},
        "matchesOrbitPrediction": dict(wd) == predicted,
        "isThreeWeight": len(wd) == 3,
        "sumIsQ5": sum(wd.values()) + 1 == q ** 5,
        "minimumDistance": min(wd),
        "sectionSizes": {"tangent": tangent, "hyperbolic": hyp, "elliptic": ell},
        "largestSectionIsHyperbolic": hyp == max(tangent, hyp, ell),
        # Cardinali-Giuzzi Main Theorem at n = k = 2
        "cgN": (q ** 4 - 1) // (q - 1),
        "cgK": 2 * 2 * 2 - 2 - 1,
        "cgD": q ** 3 - q,
        "matchesCardinaliGiuzzi": (n == (q ** 4 - 1) // (q - 1)
                                   and min(wd) == q ** 3 - q),
        "minWeightIsHyperbolicOrbit": wd[n - hyp] == (q - 1) * orbH,
    }


def main():
    rows = [study(q) for q in (3, 5, 7)]

    print("THE ORBIT CENSUS IS A PUBLISHED CODE")
    print("=" * 72)
    print("  ae04deb's exhaustive orbit census over ker(omega) and the weight")
    print("  enumerator of the quadric's projective code are the same numbers.")
    print()
    print("     q      code       weights (weight: multiplicity)")
    for r in rows:
        print("    %2d  [%3d, 5, %3d]   %s"
              % (r["q"], r["N"], r["minimumDistance"],
                 r["weightDistribution"]))
    print("  three weights, matching the orbit prediction: %s"
          % all(r["matchesOrbitPrediction"] and r["isThreeWeight"]
                for r in rows))
    print("  They HAD to match: a codeword is a functional on W, its weight is")
    print("  N - |H cap Q|, and H = p^perp by the polarity, so the weight")
    print("  depends only on the ORBIT of p.")
    print()
    print("  AND THE CODE IS PUBLISHED. Cardinali & Giuzzi, 'Minimum distance")
    print("  of Symplectic Grassmann codes', arXiv:1503.05456, Linear Algebra")
    print("  Appl. 488 (2016) 124-134. Main Theorem, at n = k = 2:")
    print("     q     N = (q^4-1)/(q-1)   K = 2n^2-n-1   d = q^{4n-5}-q^{2n-3}")
    for r in rows:
        print("    %2d          %4d              %d                %4d"
              % (r["q"], r["cgN"], r["cgK"], r["cgD"]))
    print("  matches this computation: %s"
          % all(r["matchesCardinaliGiuzzi"] for r in rows))
    print("  Since k = n = 2 this is the Lagrangian-Grassmannian code of rank")
    print("  2, whose FULL WEIGHT ENUMERATOR their abstract says they provide.")
    print("  So the enumerator above is THEIRS. No novelty is claimed for the")
    print("  code, its parameters, or its weight distribution.")
    print()
    print("  THIS IS FAILURE MODE FIVE, CAUGHT BEFORE THE CLAIM: correct")
    print("  mathematics, sound witnesses, and false novelty. Recorded so the")
    print("  corpus carries the citation rather than the coincidence.")
    print()
    print("  WHAT IS OURS, SMALL BUT REAL: a one-line derivation of their d.")
    print("  The three sections of Q(4,q) have sizes q^2+q+1, (q+1)^2, q^2+1,")
    print("  and (q+1)^2 is largest for every q, so")
    print("     d = N - (q+1)^2 = q^3 - q,")
    print("  and the maximum-section hyperplanes are exactly the hyperbolic")
    print("  orbit -- so THE MINIMUM-WEIGHT CODEWORDS ARE THE OCTET SECTIONS")
    print("  of c9e6be7: %s"
          % all(r["minWeightIsHyperbolicOrbit"] for r in rows))

    ok = all(r["matchesOrbitPrediction"] and r["isThreeWeight"]
             and r["sumIsQ5"] and r["matchesCardinaliGiuzzi"]
             and r["largestSectionIsHyperbolic"]
             and r["minWeightIsHyperbolicOrbit"] for r in rows)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "orbit_census_is_a_published_code.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.orbit-census-published-code.v1",
                "valid": bool(ok),
                "theFind": ("the exhaustive O(5,q) orbit census reported in "
                            "ae04deb and the weight enumerator of the projective "
                            "code of the quadric Q(4,q) are the same numbers, "
                            "because a codeword is a linear functional on W whose "
                            "weight is N - |H cap Q|, and H = p^perp by the "
                            "polarity, so the weight depends only on the orbit of "
                            "p: three orbits, three weights, multiplicity (q-1) "
                            "times the orbit size"),
                "rows": rows,
                "priorArt": ("Ilaria Cardinali and Luca Giuzzi, 'Minimum distance "
                             "of Symplectic Grassmann codes', arXiv:1503.05456, "
                             "Linear Algebra and its Applications 488 (2016) "
                             "124-134. Their Main Theorem gives N = prod_{i=0}^"
                             "{k-1}(q^{2n-2i}-1)/(q^{i+1}-1), K = C(2n,k) - "
                             "C(2n,k-2), and for k = 2 minimum distance "
                             "q^{4n-5} - q^{2n-3}. At n = k = 2 this is "
                             "N = (q^4-1)/(q-1), K = 5, d = q^3 - q, i.e. exactly "
                             "[40,5,24], [156,5,120], [400,5,336]. Since k = n "
                             "this is simultaneously a line Symplectic Grassmann "
                             "code and the Lagrangian-Grassmannian code of rank "
                             "2, whose FULL WEIGHT ENUMERATOR the abstract states "
                             "they provide"),
                "noNoveltyClaimed": ("none for the code, its parameters, or its "
                                     "weight distribution -- all of that is "
                                     "Cardinali-Giuzzi"),
                "failureModeFive": ("CLAUDE.md's most expensive failure mode is "
                                    "rediscovery: correct mathematics, sound "
                                    "witnesses, proportionate framing, and false "
                                    "novelty. Every number in the census is right "
                                    "and none of it is new. This file exists so "
                                    "the corpus carries the citation rather than "
                                    "the coincidence"),
                "whatIsOurs": ("a one-line geometric derivation of their minimum "
                               "distance: the three hyperplane sections of Q(4,q) "
                               "are the tangent cone, the hyperbolic section and "
                               "the elliptic section, of sizes q^2+q+1, (q+1)^2 "
                               "and q^2+1; (q+1)^2 is the largest for every "
                               "q > 0, so d = N - (q+1)^2 = q^3 - q, which is "
                               "their q^{4n-5} - q^{2n-3} at n = 2. And the "
                               "maximum-section hyperplanes are exactly the "
                               "hyperbolic orbit, so THE MINIMUM-WEIGHT CODEWORDS "
                               "ARE THE OCTET SECTIONS of c9e6be7 -- the same "
                               "objects carrying the K(q+1,q+1) grids, the 2(q+1) "
                               "thick points, and at q = 3 only the (c,m) "
                               "minimum-blocker labels of aa42b38"),
                "theKleinCorrespondence": ("Lambda^2(F^4) with the Pfaffian IS "
                                           "the Klein correspondence: lines of "
                                           "PG(3,q) <-> points of the Klein "
                                           "quadric Q+(5,q). Fixing the "
                                           "alternating form omega selects the "
                                           "hyperplane ker(omega), and "
                                           "Q(4,q) = Q+(5,q) cap ker(omega), "
                                           "whose points are exactly the totally "
                                           "isotropic lines -- W(3,q). The whole "
                                           "apparatus is the Klein correspondence "
                                           "with one bivector fixed"),
                "theTwistorDictionary": {
                    "twistor space PG(3,C)": "PG(3,q)",
                    "compactified complexified Minkowski space": "Klein quadric Q+(5,q)",
                    "infinity twistor": "omega",
                    "conformal group broken to Poincare":
                        "Q+(5,q) -> Q(4,q), i.e. Sp(4,q) = O(5,q)",
                    "status": ("a STRUCTURAL ANALOGY, not a physical claim: no "
                               "metric, no signature, no real form, nothing about "
                               "field equations. What it does say is where the "
                               "corpus's five-space came from"),
                },
                "andItClosesTheRankStory": ("the Klein correspondence exists "
                                            "because the Pfaffian on Lambda^2(F^4) "
                                            "has degree 2, which is the same fact "
                                            "ae04deb isolated as the reason the "
                                            "polar apparatus is rank-two only and "
                                            "c6d1077 continued as the reason rank "
                                            "3 is a cubic Jordan algebra. Twistor "
                                            "theory's attachment to four "
                                            "dimensions and this corpus's rank "
                                            "ceiling are one statement: Gr(2,4) "
                                            "is a quadric and Gr(2,6) is not"),
                "boundary": ("q = 3, 5, 7, exhaustive over all q^5 codewords, so "
                             "the weight distributions are ENUMERATIONS not "
                             "samples. The identification with Cardinali-Giuzzi "
                             "is by their Main Theorem's N, K and d, quoted from "
                             "the paper and matched against the computation; "
                             "their weight-enumerator section is cited from the "
                             "abstract's statement rather than transcribed, so "
                             "'the enumerator is theirs' is an attribution made "
                             "on the strength of matching parameters plus the "
                             "abstract, NOT a line-by-line comparison. Three "
                             "weights is a consequence of three orbits and is not "
                             "by itself evidence of anything. The twistor "
                             "dictionary is an analogy of structures with no "
                             "claim about physics. q even is excluded throughout: "
                             "there the symplectic and orthogonal pictures differ "
                             "and K is 6, not 5. Nothing here touches tau_2"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
