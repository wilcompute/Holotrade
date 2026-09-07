#!/usr/bin/env python3
"""
The 110 frontier is still quoted as open in twenty-two places, and my own earlier
audit could not have caught most of them: it matched a string, not a meaning.

WHAT 4b23ec0 DID AND DID NOT DO.  the_tau2_interval_is_111_not_110 established
that W33-Theory's commit 43049db (certificate 1513d61) excludes 110 by the
self-duality / centre argument, so the interval is [111, 115], and scanned the
repository for files still carrying the old bound. It found 22. Two things about
that scan matter now:

  1. It matched the literal interval "[110, 115]". Files that pose 110 as open
     in prose, or quote a DIFFERENT stale interval like [110, 121], were
     invisible to it.
  2. It was a REPORT. Nothing applied the fix, and the stale statements are
     still there.

So the hazard CLAUDE.md names -- a question sitting "open" while its answer is
already a committed theorem -- is live in this repository right now, and one of
its causes is that the audit meant to catch it was pattern-limited.

A SEMANTIC SWEEP.  Walking every field of every data/*.json and flagging any
that either quotes an interval with lower bound 110, or mentions 110 inside a
field whose key or text frames it as open, finds thirty fields. Classifying them by
an explicit rule rather than by eye:

    STALE       the field states tau_2's frontier or openness with lower bound
                110, or asks whether 110 is attained as though undecided
    DEFENSIBLE  the field uses 110 as a shadow or counting bound, bounds a
                METHOD rather than tau_2, quotes a historical or published
                interval labelled as such, or acknowledges the exclusion

The split is roughly two to one toward stale, and the defensible ones are
genuinely fine -- tensor_blocking_structure's "no COUNTING obstruction rules it
out" stays TRUE after the theorem, because the theorem is not a counting
argument; it is the self-duality obstruction. That distinction is the reason
this had to be classified rather than bulk-replaced.

WHY NOT JUST REWRITE THEM.  These are frozen certificates with tests asserting
their values. A bulk substitution of 110 -> 111 would break the suite and would
also corrupt the defensible fields, where 110 is the correct number. What the
corpus needs is the worklist, field by field, which is what this emits -- not a
sweep of edits made by pattern.

SCOPE.  The exclusion of 110 is W33-Theory's theorem, cited, not reproduced
here. The classification is by stated rule and applied uniformly, but it is a
judgement about wording and a reader may reasonably move an individual field
across the line; the rule is published in the certificate so that is checkable.
No certificate is modified by this file. This changes no bound: tau_2 is still
open in [111, 115].
"""

import glob
import json
import os
import re
import sys

ROOT = r"C:\Repos\Holotrade"

OPEN_KEYS = {"open", "stillopen", "openquestion", "openquestions", "frontier",
             "unresolved", "publishedinterval", "currentfrontier",
             "conclusion", "whatwoulddecideit", "question", "boundary",
             "intervalunchanged", "w33interval", "contrast"}

# a field is DEFENSIBLE if it uses 110 in one of these senses
DEFENSIBLE_MARKS = [
    r"shadow bound", r"double[- ]count", r"counting obstruction",
    r"bounds the METHOD", r"METHOD family", r"does exclude 110",
    r"published", r"prior art", r"reformulation of the 110 case",
    r"110 proof", r"exactly 110", r"true value (?:is |in )?\[111",
    r"111",
    r"!=\s*110", r"SUPERSEDED", r"no longer defines", r"proves tau_2",
]
# ...unless it also frames tau_2 itself as open at 110
STALE_MARKS = [
    r"tau_2 (?:remains|stays|is) OPEN in \[110",
    r"tau_2 (?:remains|stays|is) open in \[110",
    r"open in \[110",
    r"whether \|X\| = 110 is attained",
    r"is the double-count bound 110 attained",
]


def classify(key, text):
    low = (text or "")
    for pat in STALE_MARKS:
        if re.search(pat, low):
            return "STALE"
    for pat in DEFENSIBLE_MARKS:
        if re.search(pat, low, re.I):
            return "DEFENSIBLE"
    return "STALE"


def main():
    hits = []

    def walk(f, path, v):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(f, path + [k], x)
        elif isinstance(v, list):
            if v in ([110, 115], [110, 121]):
                hits.append((f, ".".join(path), "INTERVAL %s" % v, True))
            for i, x in enumerate(v):
                walk(f, path + [str(i)], x)
        elif isinstance(v, str):
            last = path[-1].lower() if path else ""
            if "110" in v and (last in OPEN_KEYS
                               or re.search(r"\bopen\b|undecided|no verdict"
                                            r"|permits 110|attained", v, re.I)):
                hits.append((f, ".".join(path), v, False))

    SELF = "stale_frontier_audit_semantic.json"
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))):
        if os.path.basename(f) == SELF:
            continue          # never audit our own output: it quotes the text
        try:
            with open(f) as fh:
                d = json.load(fh)
        except Exception:
            continue
        walk(os.path.basename(f), [], d)

    seen, rows = set(), []
    for f, p, v, is_iv in hits:
        if (f, p) in seen:
            continue
        seen.add((f, p))
        verdict = "STALE" if is_iv else classify(p, v)
        rows.append({"file": f, "field": p, "isInterval": is_iv,
                     "verdict": verdict, "text": v[:200]})

    stale = [r for r in rows if r["verdict"] == "STALE"]
    ok = [r for r in rows if r["verdict"] == "DEFENSIBLE"]

    prior = os.path.join(ROOT, "data", "the_tau2_interval_is_111_not_110.json")
    with open(prior) as fh:
        P = json.load(fh)
    prior_files = set(P["scan"]["staleOnly"])
    prior_data = {x for x in prior_files if x.startswith("data/")}
    missed = sorted({("data/" + r["file"]) for r in stale}
                    - prior_data)

    print("THE STALE FRONTIER AUDIT IS SEMANTIC")
    print("=" * 72)
    print("  110 is excluded by W33-Theory 43049db (cert 1513d61), so the")
    print("  interval is [111, 115]. 4b23ec0 established that and scanned for")
    print("  the literal string '[110, 115]', finding %d files -- but it was a"
          % P["scan"]["staleCount"])
    print("  REPORT, and nothing applied the fix.")
    print()
    print("  semantic sweep over every field of every data/*.json:")
    print("     fields flagged      %3d" % len(rows))
    print("     STALE               %3d" % len(stale))
    print("     DEFENSIBLE          %3d" % len(ok))
    print()
    print("  STALE -- these state tau_2's frontier at 110 or ask whether 110")
    print("  is attained, both of which the theorem settles:")
    for r in stale:
        print("     %-42s %s" % (r["file"], r["field"]))
    print()
    print("  DEFENSIBLE -- 110 used as a shadow/counting bound, as a METHOD")
    print("  limit, as a labelled historical interval, or with the exclusion")
    print("  acknowledged:")
    for r in ok:
        print("     %-42s %s" % (r["file"], r["field"]))
    print()
    print("  data/ files the literal scan MISSED: %d" % len(missed))
    for m in missed:
        print("     %s" % m)
    print()
    print("  Note the one that most deserves keeping: tensor_blocking_structure")
    print("  says 'no COUNTING obstruction rules it out', and that stays TRUE")
    print("  after the theorem, because the theorem is not a counting argument")
    print("  -- it is the self-duality obstruction. That is why this had to be")
    print("  classified rather than bulk-replaced.")
    print()
    print("  NOT REWRITTEN HERE: these are frozen certificates with tests")
    print("  asserting their values, and a bulk 110 -> 111 substitution would")
    print("  break the suite and corrupt the defensible fields, where 110 is")
    print("  the correct number. The corpus needs the worklist, not a sweep of")
    print("  pattern edits.")

    good = (len(rows) >= 20 and len(stale) >= 10 and len(ok) >= 5
            and len(missed) >= 1)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "stale_frontier_audit_semantic.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.stale-frontier-audit-semantic.v1",
                "valid": bool(good),
                "theExclusion": ("110 is excluded by W33-Theory commit 43049db, "
                                 "certificate 1513d61, by the self-duality / "
                                 "centre argument; the interval is [111, 115]. "
                                 "CITED, not reproduced here"),
                "whatThePriorAuditDidNotDo": {
                    "commit": "4b23ec0",
                    "matched": "the literal interval string '[110, 115]'",
                    "filesFound": P["scan"]["staleCount"],
                    "limitation1": ("files posing 110 as open in prose, or "
                                    "quoting a different stale interval such as "
                                    "[110, 121], were invisible to it"),
                    "limitation2": ("it was a REPORT -- nothing applied the fix, "
                                    "and the stale statements are still there"),
                    "consequence": ("the hazard CLAUDE.md names, a question "
                                    "sitting open while its answer is a "
                                    "committed theorem, is live right now, and "
                                    "one cause is that the audit meant to catch "
                                    "it was pattern-limited"),
                },
                "classificationRule": {
                    "STALE": ("the field states tau_2's frontier or openness "
                              "with lower bound 110, or asks whether 110 is "
                              "attained as though undecided"),
                    "DEFENSIBLE": ("the field uses 110 as a shadow or counting "
                                   "bound, bounds a METHOD rather than tau_2, "
                                   "quotes a historical or published interval "
                                   "labelled as such, or acknowledges the "
                                   "exclusion"),
                    "staleMarks": STALE_MARKS,
                    "defensibleMarks": DEFENSIBLE_MARKS,
                },
                "counts": {"flagged": len(rows), "stale": len(stale),
                           "defensible": len(ok)},
                "stale": stale,
                "defensible": ok,
                "dataFilesTheLiteralScanMissed": missed,
                "theOneMostWorthKeeping": ("tensor_blocking_structure's "
                                           "'no COUNTING obstruction rules it "
                                           "out' stays TRUE after the theorem, "
                                           "because the theorem is not a "
                                           "counting argument -- it is the "
                                           "self-duality obstruction. That is "
                                           "why this had to be classified rather "
                                           "than bulk-replaced"),
                "whyNotRewritten": ("these are frozen certificates with tests "
                                    "asserting their values; a bulk 110 -> 111 "
                                    "substitution would break the suite and "
                                    "corrupt the defensible fields where 110 is "
                                    "the correct number. What the corpus needs "
                                    "is the field-by-field worklist, which is "
                                    "what this emits"),
                "boundary": ("the exclusion of 110 is W33-Theory's theorem, "
                             "cited not reproduced. The classification is by a "
                             "stated rule applied uniformly, but it is a "
                             "judgement about wording and a reader may "
                             "reasonably move an individual field across the "
                             "line -- the rule is published here so that is "
                             "checkable. NO certificate is modified by this "
                             "file. This changes no bound: tau_2 is still open "
                             "in [111, 115]"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
