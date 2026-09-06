#!/usr/bin/env python3
"""
This track had ZERO references to the finite-geometry / qubit literature while
the other track had thirty-one. That asymmetry is what produced today's
near-miss, and it is a protocol gap, not a discipline one.

WHAT HAPPENED.  ea2ff88 identified the 45 monomials of the E6 Cartan cubic with
the 45 lines of GQ(2,4), recorded a corpus search that found nothing, hedged the
novelty correctly, and was still wrong to imply any. The result is published:
Levay, Saniga and Vrana, arXiv:0903.0541, say it in one sentence, and the whole
three-member Jordan/GQ series with it. 4b92d42 withdrew the hedge.

The interesting part is not that it happened. It is where the citation already
was.

THE ASYMMETRY, MEASURED.  Counting analysis files that mention Saniga, Planat,
Levay or Veldkamp:

    Holotrade (this track)            0
    Theory-of-Everything              31

The other track has been citing this literature all along, by name and by
number -- arXiv:0903.0715 for the Veldkamp space of GQ(2,4), quant-ph/0611063
for Saniga-Planat-Pracna's projective-ring model of the two-qubit Pauli
geometry, and a long list besides. This track had none of it. So the near-miss
was not a failure to search; the corpus's own answer was one repository away and
the search never looked there.

WHY THE EXISTING PROTOCOL DID NOT CATCH IT.  CLAUDE.md's cross-track rule is
about FILES: regenerate RESULTS_INDEX.md, run check_rediscovery.py, grep the
other track's results before claiming novelty. All of that is about internal
results. None of it covers the other track's EXTERNAL references, and external
references are exactly what settles novelty. The two tracks can each be perfectly
disciplined about internal prior art and still have one of them blind to a
literature the other reads daily.

THE AMENDMENT THIS SUGGESTS.  Before claiming novelty, grep the other track for
the author names and arXiv identifiers near the object, not only for the object.
A single `grep -rl "Saniga\|Levay\|Veldkamp"` on the other repository would have
returned thirty-one files today and stopped ea2ff88's framing before it was
written. That costs one command.

AND WHERE THE FRONTIER ACTUALLY IS.  The same searching separates this session's
work cleanly into two piles, which is worth stating because the piles are not
what they look like from inside:

    PUBLISHED, and now cited rather than claimed
      the Jordan/Severi series and its GQ monomial structures  (0903.0541;
        Comm. Algebra 29(10) 2001)
      the line Symplectic Grassmann codes and their parameters (Cardinali-Giuzzi,
        arXiv:1503.05456)
      the association scheme on anisotropic points               (Adriaensen-De
        Boeck, arXiv:2402.05055)
      W(E6) = U4(2):2 = PSp(4,3).2, GQ(3,3) classification       (classical)

    NO LITERATURE FOUND, so plausibly the real frontier
      tau_2 for W(3,3) tensor W(3,3): a search for blocking numbers of PRODUCTS
        of generalized quadrangles returns work on blocking sets in single
        quadrangles and nothing on products. The corpus reached the same
        conclusion independently in tensor_multiplicativity_ovoid_defect.json,
        which records "no literature on blocking numbers of products of
        generalized quadrangles turned up".

So the ornamental results of this session -- E6, Jordan, the quadrangles -- are
the classical ones, and the stubborn central problem is the one that appears to
be genuinely open. That is the opposite of how it felt while working, which is
the whole reason to write it down.

SCOPE.  The counts are grep counts over analysis/ in each repository at the time
of running, for four author/term strings; they measure citation PRESENCE, not
whether any particular citation is apt, and a file mentioning "Veldkamp" is
counted the same as one building on it. "No literature found" is a statement
about searches performed, never a proof of absence -- it is the weakest kind of
evidence and is recorded as such. The published/open split above is a reading of
search results, not an audit of the fields.
"""

import json
import os
import re
import subprocess
import sys

ROOT = r"C:\Repos\Holotrade"
OTHER = r"C:\Repos\Theory of Everything"
TERMS = ["Saniga", "Planat", "Levay", "Veldkamp"]
MINE_TODAY = ("jordan_gq_series_is_published", "schlafli_triangle_is_one_polynomial",
              "other_track_had_the_citations")


def count(repo):
    d = os.path.join(repo, "analysis")
    if not os.path.isdir(d):
        return None, []
    hits = []
    pat = re.compile("|".join(TERMS))
    for dirpath, _, files in os.walk(d):
        for fn in files:
            if not fn.endswith((".py", ".md")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    if pat.search(fh.read()):
                        hits.append(fn)
            except OSError:
                pass
    return len(hits), sorted(hits)


def main():
    mine_n, mine = count(ROOT)
    mine_prior = [f for f in mine if not any(t in f for t in MINE_TODAY)]
    other_n, other = count(OTHER)

    print("THE OTHER TRACK HAD THE CITATIONS")
    print("=" * 72)
    print("  analysis files mentioning %s:" % ", ".join(TERMS))
    print("     Holotrade (this track), excluding today's files : %d"
          % len(mine_prior))
    print("     Theory-of-Everything                            : %s"
          % (other_n if other_n is not None else "unavailable"))
    print()
    print("  ea2ff88 searched THIS repository, found nothing, hedged, and was")
    print("  still wrong to imply novelty -- the result is Levay-Saniga-Vrana,")
    print("  arXiv:0903.0541. The citation was one repository away.")
    print()
    print("  WHY THE PROTOCOL MISSED IT: CLAUDE.md's cross-track rule is about")
    print("  FILES and internal RESULTS -- the index, the rediscovery hook,")
    print("  grepping the other track's results. None of that covers the other")
    print("  track's EXTERNAL references, which are what settle novelty. Both")
    print("  tracks can be disciplined about internal prior art and one still")
    print("  be blind to a literature the other reads daily.")
    print()
    print("  AMENDMENT: before claiming novelty, grep the other track for the")
    print("  AUTHOR NAMES and arXiv ids near the object, not only the object.")
    print("  One command today would have returned %s files and stopped the"
          % (other_n if other_n is not None else "many"))
    print("  framing before it was written.")
    print()
    print("  AND WHERE THE FRONTIER IS. Published and now cited: the Jordan/")
    print("  Severi series and its GQ monomial structures; the line Symplectic")
    print("  Grassmann codes; the anisotropic association scheme; the classical")
    print("  group isomorphisms. No literature found: tau_2 for the W(3,3)")
    print("  tensor square -- searches return blocking sets in SINGLE")
    print("  quadrangles and nothing on products, which is where the corpus")
    print("  independently landed too. The ornamental results are the classical")
    print("  ones and the stubborn central problem is the open one, which is")
    print("  the opposite of how it felt from inside.")

    ok = (mine_prior == [] and other_n is not None and other_n >= 10)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "other_track_had_the_citations.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.cross-track-citation-gap.v1",
                "valid": bool(ok),
                "terms": TERMS,
                "holotradeFilesExcludingToday": len(mine_prior),
                "holotradeFilesToday": len(mine) - len(mine_prior),
                "theoryOfEverythingFiles": other_n,
                "whatHappened": ("ea2ff88 identified the 45 monomials of the E6 "
                                 "Cartan cubic with the 45 lines of GQ(2,4), "
                                 "recorded a corpus search that found nothing, "
                                 "hedged the novelty correctly, and was still "
                                 "wrong to imply any: the result is "
                                 "Levay-Saniga-Vrana, arXiv:0903.0541, and the "
                                 "whole three-member Jordan/GQ series with it. "
                                 "4b92d42 withdrew the hedge. The interesting "
                                 "part is not that it happened but where the "
                                 "citation already was"),
                "whyTheProtocolMissedIt": ("CLAUDE.md's cross-track rule is about "
                                           "FILES and internal RESULTS -- "
                                           "regenerate the index, run the "
                                           "rediscovery hook, grep the other "
                                           "track's results before claiming "
                                           "novelty. None of that covers the "
                                           "other track's EXTERNAL references, "
                                           "and external references are exactly "
                                           "what settle novelty. Both tracks can "
                                           "be perfectly disciplined about "
                                           "internal prior art and one still be "
                                           "blind to a literature the other reads "
                                           "daily"),
                "theAmendment": ("before claiming novelty, grep the OTHER track "
                                 "for the author names and arXiv identifiers near "
                                 "the object, not only for the object itself. A "
                                 "single grep for Saniga, Planat, Levay or "
                                 "Veldkamp on the other repository would have "
                                 "returned thirty-one files today and stopped "
                                 "ea2ff88's framing before it was written. It "
                                 "costs one command"),
                "publishedAndNowCited": {
                    "jordanSeveriSeriesAndGQMonomials":
                        "arXiv:0903.0541; Comm. Algebra 29(10) (2001)",
                    "lineSymplecticGrassmannCodes":
                        "Cardinali-Giuzzi, arXiv:1503.05456",
                    "anisotropicAssociationScheme":
                        "Adriaensen-De Boeck, arXiv:2402.05055",
                    "groupIsomorphismsAndGQClassification":
                        "classical (W(E6) = U4(2):2 = PSp(4,3).2; Payne-Thas)",
                },
                "noLiteratureFound": {
                    "tau2ForTheW33TensorSquare": ("a search for blocking numbers "
                                                  "of PRODUCTS of generalized "
                                                  "quadrangles returns work on "
                                                  "blocking sets in single "
                                                  "quadrangles and nothing on "
                                                  "products; the corpus reached "
                                                  "the same conclusion "
                                                  "independently in "
                                                  "tensor_multiplicativity_ovoid_"
                                                  "defect.json, which records 'no "
                                                  "literature on blocking numbers "
                                                  "of products of generalized "
                                                  "quadrangles turned up'"),
                },
                "theUncomfortableReading": ("the ornamental results of this "
                                            "session -- E6, Jordan, the "
                                            "quadrangles -- are the classical "
                                            "ones, and the stubborn central "
                                            "problem is the one that appears "
                                            "genuinely open. That is the opposite "
                                            "of how it felt while working, which "
                                            "is the whole reason to write it "
                                            "down"),
                "boundary": ("the counts are grep counts over analysis/ in each "
                             "repository at the time of running, for four "
                             "author/term strings; they measure citation PRESENCE, "
                             "not aptness, and a file merely mentioning "
                             "'Veldkamp' counts the same as one building on it. "
                             "'No literature found' is a statement about searches "
                             "performed and never a proof of absence -- the "
                             "weakest kind of evidence, recorded as such. The "
                             "published/open split is a reading of search results, "
                             "not an audit of the fields"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
