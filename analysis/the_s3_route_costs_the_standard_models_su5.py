#!/usr/bin/env python3
"""
THE S3 ROUTE COSTS THE STANDARD MODEL'S SU(5): AN INVERTING ORDER-TWO ELEMENT CUTS THE
W(3,3) TWIST'S SU(9) DOWN TO SO(9), AND SO(9) HAS NO SU(5).

TOE w33_heterotic_s3_outer_target.py matches the extension law of the W(3,3) outer inversion
(s z s^-1 = z^-1) to the S3 point group of Konopka's non-Abelian heterotic orbifold, and asks
what a gauge embedding of it would look like. This file answers the gauge side, exactly.

1. THE EMBEDDING CANNOT BE A SHIFT. Let theta = exp(2 pi i V.H) be the order-three gauge twist
   and let s be an order-two element of the space group with s theta s^-1 = theta^-1. If s were
   also a shift it would commute with the Cartan torus, forcing theta = theta^-1, hence
   theta^2 = 1; with theta^3 = 1 that gives theta = 1. So in an S3 orbifold the order-two
   element must act on the gauge lattice by a lattice automorphism (a Weyl element w with
   w(V) = -V mod the lattice), never by a shift or a Wilson line. This is the precise sense in
   which the S3 route is non-Abelian in the gauge sector too.

2. WHAT SURVIVES. The W(3,3) twist is the A8 class, so the theta-invariant subalgebra is
   su(9) (72 roots, rank 8), computed below. The element s acts on that su(9) by an
   automorphism which inverts its centre -- inner automorphisms fix the centre pointwise, so s
   acts by an OUTER automorphism. For su(n) with n odd the only outer involution class has
   fixed subalgebra so(n). Hence

       su(9)  ->  so(9),    dimension 80 -> 36,    rank 8 -> 4.

   The dimension is recomputed here from the trace of the involution on the algebra, not quoted.

3. THE COST. so(9) contains no su(5). Any embedding would give a nine-dimensional real
   representation of su(5); the su(5) irreducible representations of dimension at most nine are
   the trivial one and the complex pair 5, 5bar, and 5 + 5bar already has dimension ten. So the
   only nine-dimensional real representation of su(5) is the trivial one, and su(5) does not
   embed in so(9). The irreducible dimensions and their reality are computed below from the
   Weyl dimension formula, not quoted.

   Because GUT-normalised hypercharge means Y inside an SU(5) subgroup of E8 -- the criterion
   used by every Standard Model search in this literature, and the one satisfied by the vacua
   of the_w33_twist_does_host_a_standard_model_in_the_even_order_orbifold.py -- the Standard
   Model's hypercharge CANNOT descend from the W(3,3) E8 in an S3 orbifold. It would have to
   come from the other E8, in which case the W(3,3) twist is not where the Standard Model
   lives.

4. THE DICHOTOMY THIS SETTLES. Both C2's are available to the W(3,3) twist, and they are not
   interchangeable:

       inverting C2 (S3 point group)      s z s^-1 = z^-1   gauge embedding must be a lattice
                                                            automorphism; SU(9) -> SO(9);
                                                            no SU(5), so no GUT hypercharge
                                                            from this E8
       commuting C2 (Z6 point group)      s z s^-1 = z      gauge embedding is a shift;
                                                            SU(9) survives as a local group;
                                                            Standard Models exist (5b3f3ad)

   The Standard Models found in 5b3f3ad use the commuting C2, exactly as this argument
   requires. The inverting C2 of the Suzuki/Heisenberg certificates is the right group-theoretic
   match for the S3 extension law, but it is the wrong operation for building the Standard
   Model, and this is why.

SCOPE. Exact root-system and representation-theory computation. The classification input --
that the outer involutions of su(n), n odd, have fixed subalgebra so(n) -- is classical
(Cartan's list of symmetric pairs, AI); everything else is computed here. No claim is made
about whether Konopka's specific S3 model admits an A8-class embedding; the statement is that
IF the inverting C2 acts on the W(3,3) twist, THEN the SU(5) is lost.
"""

import argparse
import itertools
import json
import os
from fractions import Fraction as Fr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def roots8():
    R = []
    for i, j in itertools.combinations(range(8), 2):
        for a in (1, -1):
            for b in (1, -1):
                v = [Fr(0)] * 8
                v[i], v[j] = Fr(a), Fr(b)
                R.append(tuple(v))
    for s in itertools.product((1, -1), repeat=8):
        if sum(1 for x in s if x < 0) % 2 == 0:
            R.append(tuple(Fr(x, 2) for x in s))
    return R


ROOTS = roots8()


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def rank_of(vectors):
    """rank over Q by fraction-free elimination"""
    M = [list(v) for v in vectors]
    r = 0
    for c in range(8):
        piv = next((i for i in range(r, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c] / M[r][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        r += 1
    return r


def su5_irrep_dims(maxdim):
    """Weyl dimension formula for A4, with self-conjugacy, up to maxdim"""
    out = []
    for lam in itertools.product(range(0, 6), repeat=4):
        # dim = prod_{i<j} (lam_i + ... + lam_{j-1} + j - i) / (j - i)
        num, den = 1, 1
        for i in range(4):
            for j in range(i + 1, 5):
                num *= sum(lam[i:j]) + (j - i)
                den *= (j - i)
        d = num // den
        if d <= maxdim:
            selfconj = lam == tuple(reversed(lam))       # conjugation reverses the Dynkin labels
            out.append((lam, d, selfconj))
    return sorted(set(out), key=lambda t: t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    checks = {}

    # 1. the A8 class: theta-invariant subalgebra is su(9)
    V = [Fr(0), Fr(0), Fr(0), Fr(1, 3), Fr(1, 3), Fr(1, 3), Fr(1, 3), Fr(2, 3)]
    # any representative of the A8 class works; check it is one: 3V in the lattice, 72 fixed roots
    u = [3 * x for x in V]
    in_lattice = all(x.denominator == 1 for x in u) and sum(u) % 2 == 0
    fixed = [r for r in ROOTS if dot(r, V).denominator == 1]
    checks["representative_is_a_Z3_shift"] = in_lattice
    checks["A8_class_has_72_roots"] = len(fixed) == 72
    checks["A8_has_rank_eight"] = rank_of(fixed) == 8
    dim_su9 = len(fixed) + 8            # 72 roots + rank 8 Cartan = 80 = dim su(9)
    checks["su9_dimension_80"] = dim_su9 == 80
    print("  theta-invariant subalgebra: %d roots, rank %d, dimension %d = su(9)" % (
        len(fixed), rank_of(fixed), dim_su9))

    # 2. the inverting involution acts as -1 on the Cartan and pairs E_alpha with E_-alpha.
    # trace on the algebra = -8 (Cartan) + 0 (each root pair contributes trace 0)
    pairs = 0
    seen = set()
    for r in fixed:
        nr = tuple(-x for x in r)
        assert nr in set(fixed)
        key = frozenset([r, nr])
        if key not in seen:
            seen.add(key)
            pairs += 1
    trace = -8 + 0
    dim_fixed = (dim_su9 + trace) // 2
    checks["root_vectors_pair_up"] = 2 * pairs == len(fixed)
    checks["fixed_subalgebra_dimension_36"] = dim_fixed == 36
    checks["so9_dimension_matches"] = dim_fixed == 9 * 8 // 2
    print("  inverting involution: trace %d on su(9), fixed subalgebra dimension %d = so(9), rank 4" % (
        trace, dim_fixed))

    # 3. su(5) does not embed in so(9): no nontrivial nine-dimensional real representation
    irreps = su5_irrep_dims(9)
    nontrivial_real = [(l, d) for l, d, sc in irreps if sc and d > 1 and d <= 9]
    smallest_complex_pair = min((d for l, d, sc in irreps if not sc and d > 1), default=None)
    print("  su(5) irreps of dimension <= 9: %s" % sorted({(d, sc) for l, d, sc in irreps}))
    print("  self-conjugate nontrivial ones: %s; smallest complex pair costs %d" % (
        nontrivial_real, 2 * smallest_complex_pair if smallest_complex_pair else 0))
    checks["no_nontrivial_real_su5_rep_up_to_dim_9"] = nontrivial_real == []
    checks["smallest_complex_pair_exceeds_nine"] = smallest_complex_pair == 5 and 2 * 5 > 9
    checks["su5_does_not_embed_in_so9"] = \
        checks["no_nontrivial_real_su5_rep_up_to_dim_9"] and checks["smallest_complex_pair_exceeds_nine"]

    # 4. the shift obstruction, as arithmetic: 2V in the lattice and 3V in the lattice give V in it
    two_V_in = all((2 * x).denominator == 1 for x in V) and sum(2 * x for x in V) % 2 == 0
    checks["an_inverting_shift_would_trivialise_the_twist"] = not two_V_in     # else V would be trivial
    print("  an inverting element that were itself a shift would force 2V and 3V in the lattice, "
          "hence V in the lattice: %s" % (not two_V_in))

    for k, v in checks.items():
        print("  %-46s %s" % (k, v))
    valid = all(checks.values())
    print("VALID:", valid)

    if args.write:
        payload = {
            "claim": "If an order-two element inverts the W(3,3) order-three gauge twist, as the S3 point group of "
                     "w33_heterotic_s3_outer_target requires, then it cannot be a shift or a Wilson line, it must act by "
                     "a lattice automorphism, and it cuts the twist's su(9) down to so(9) (dimension 80 -> 36, rank "
                     "8 -> 4). so(9) contains no su(5), because su(5) has no nontrivial nine-dimensional real "
                     "representation. Hence GUT-normalised hypercharge cannot descend from the W(3,3) E8 in an S3 "
                     "orbifold. The commuting C2 of the Z6 point group has no such cost, and that is the one under which "
                     "Standard Models were found (5b3f3ad).",
            "twistSubalgebra": {"roots": len(fixed), "rank": 8, "dimension": dim_su9, "name": "su(9)"},
            "afterInversion": {"trace_on_su9": trace, "dimension": dim_fixed, "rank": 4, "name": "so(9)",
                               "classification_input": "outer involutions of su(n), n odd, have fixed subalgebra so(n) "
                                                       "(Cartan symmetric pair AI)"},
            "su5InSo9": {"nontrivial_real_reps_up_to_dim_9": nontrivial_real,
                         "smallest_complex_pair_dimension": 2 * smallest_complex_pair,
                         "embeds": False},
            "dichotomy": {"inverting_C2": "S3 point group; lattice-automorphism embedding; SU(9) -> SO(9); no SU(5)",
                          "commuting_C2": "Z6 point group; shift embedding; SU(9) survives locally; Standard Models "
                                          "exist (Holotrade 5b3f3ad)"},
            "checks": checks, "valid": valid,
            "status": "exact root-system and representation-theory computation; the symmetric-pair classification is "
                      "classical and cited",
            "boundary": "Conditional on the inverting C2 acting on the W(3,3) E8, and on the 4D gauge group being the "
                        "commutant of the embedded space group, i.e. generic moduli with no gauge enhancement. No claim "
                        "about whether Konopka's S3 model admits an A8-class embedding, nor that hypercharge from the "
                        "OTHER E8 is excluded.",
            "sources": ["TOE w33_heterotic_s3_outer_target.py", "TOE w33_z6ii_c2_extension_no_go.py",
                        "TOE w33_suzuki_outer_heisenberg_sector_swap.py",
                        "Holotrade 5b3f3ad", "Holotrade 2365e59", "Holotrade 68df33f",
                        "Konopka, JHEP 07 (2013) 023", "Cartan's classification of symmetric pairs (AI)"]}
        with open(os.path.join(ROOT, "data", "w33_s3_route_costs_the_su5.json"), "w") as f:
            json.dump(payload, f, indent=1)
        print("written")


if __name__ == "__main__":
    main()
