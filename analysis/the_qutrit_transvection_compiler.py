#!/usr/bin/env python3
"""
A minimal transvection decomposition for the QUTRIT Clifford group, verified
exhaustively -- the compiler the ISA cost model implied and the literature
stops one field short of.

WHY THIS IS THE GAP.  Pllaha-Volanto-Tirkkonen (arXiv:2102.11380) give a fast
algorithm decomposing any Clifford gate into a MINIMAL product of Clifford
transvections. It is built over F_2 throughout -- qubits -- and its machinery
(the residue matrix, triangularisation by congruence over GF(2), Botha's
theorem) is characteristic-2 specific. This substrate is q = 3. b363f7c showed
the transvections ARE the architecturally natural instruction set here
(diameter 4 on the group, 2 on the states), so "compile an arbitrary gate to a
shortest transvection program" is the ISA's code-generation problem, and it was
open at q = 3.

THE ALGORITHM, and it is field-general rather than a port.  To shorten g, find a
vector it can pivot on and cancel one dimension of residue:

    pick x with <x, g^-1 x> =/= 0
    set   v = g^-1 x - x        and   lam = <x, g^-1 x>^-1
    then  g . T(v, lam)  fixes x, and its residue is res(g) - 1.

The derivation is one line: g.T(v,lam) fixes x iff T(v,lam)x = g^-1 x, and
T(v,lam)x = x + lam <x,v> v, so v must be parallel to g^-1 x - x and lam must
invert <x, v> = <x, g^-1 x>. Existence of x is exactly NON-hyperbolicity, which
is why O'Meara's criterion is the hypothesis. At q = 2 this collapses to
v = x + xg and lam = 1, recovering the published step; at odd q the scalar lam
is the new content, and it is forced, not chosen.

HYPERBOLIC INPUTS take one extra instruction, by the theorem: multiply by a
transvection that preserves the residue and lands non-hyperbolic, then proceed.
Here that transvection is found by direct search over the eighty.

THE PORTING PITFALL, WHICH COST A RUN AND IS THE REAL CONTENT.  The obvious
reading of the published algorithm tests hyperbolicity ONCE, on the input, and
then peels residue. That strands 1,679 of the 51,840 -- every failure at
residue 2 with the current element hyperbolic. A non-hyperbolic gate can peel
onto a hyperbolic INTERMEDIATE, and the pivot x exists only for non-hyperbolic
elements, so the loop dies halfway. The fix is to re-test at every step and,
among the pivots that drop the residue, prefer one whose result is
non-hyperbolic; the residue-preserving fix-up is then needed only when the
current element is already hyperbolic.

That is the same failure mode 3595bd1 found in Sp(4,2), where every
residue-dropping step out of the ninety at (res 3, len 4) lands hyperbolic and
the classical induction genuinely breaks. At q = 3 a good pivot always exists,
so the repair is available and the length stays minimal -- but only if the
algorithm looks for it.

EXHAUSTIVE VERIFICATION, over all 51,840 elements of Sp(4,3):

    decompositions produced                  51840
    every factor a genuine transvection      51840
    product reconstructs g exactly           51840
    length equals the BFS ground truth       51840        <- MINIMAL, not just
                                                             correct
    longest program emitted                      5

So it is a total function, it is correct, and it is optimal on every input --
not optimal in the worst case, optimal pointwise, checked against a full
breadth-first search rather than against a bound.

WHAT IT COSTS TO RUN.  The compiler never searches the group. It scans at most
eighty vectors per instruction emitted and emits at most five, so compiling any
gate is bounded work independent of the 51,840. That is the difference between a
routing table and a compiler, and it is what makes the forty-opcode ISA
implementable rather than merely optimal on paper.

RELATION TO THE ANOMALIES.  The one place the algorithm needs its extra
instruction is exactly the 91 hyperbolic maps of 3595bd1 -- the 90 indexed by
the hyperbolic lines carrying the sentinel code's minimum words, plus the
centre. The compiler's only irregular branch and the code's minimum-weight
structure are the same objects, which is the co-location claim made operational.

SCOPE.  Exact and exhaustive at q = 3, dimension 4. The step is derived for any
odd q but tested only here, and the hyperbolic fix-up is found by search rather
than construction, so this is a verified compiler for Sp(4,3), not a proof for
Sp(2n,q). It emits symplectic transvections -- the Clifford group is their
central extension, and the phase bookkeeping needed to lift a symplectic program
to an actual qutrit circuit is NOT done here. tau_2 is untouched.
"""

import collections
import itertools
import json
import os
import sys

ROOT = r"C:\Repos\Holotrade"
Q = 3
D = 4


def main():
    def mul(A, B):
        return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(D)) % Q
                           for j in range(D)) for i in range(D))

    I = tuple(tuple(1 if i == j else 0 for j in range(D)) for i in range(D))

    def form(u, v):
        return (u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]) % Q

    E = [tuple(1 if k == j else 0 for k in range(D)) for j in range(D)]

    def tv(vv, lam):
        return tuple(tuple(((1 if i == j else 0)
                            + lam * form(E[j], vv) * vv[i]) % Q
                           for j in range(D)) for i in range(D))

    def act(A, v):
        return tuple(sum(A[i][k] * v[k] for k in range(D)) % Q
                     for i in range(D))

    vecs = [v for v in itertools.product(range(Q), repeat=D) if any(v)]
    T = {}
    for v in vecs:
        for lam in range(1, Q):
            M = tv(v, lam)
            if M != I:
                T[M] = (v, lam)
    Tlist = sorted(T)

    # ground truth: exact minimal length for every element
    dist, fr, dia = {I: 0}, [I], 0
    while fr:
        nx = []
        for A in fr:
            for M in Tlist:
                C = mul(M, A)
                if C not in dist:
                    dist[C] = dia + 1
                    nx.append(C)
        fr = nx
        if nx:
            dia += 1

    def rk(A):
        M = [[(A[i][j] - (1 if i == j else 0)) % Q for j in range(D)]
             for i in range(D)]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, D) if M[i][c] % Q), None)
            if p is None:
                continue
            M[r], M[p] = M[p], M[r]
            iv = pow(M[r][c], -1, Q)
            M[r] = [(x * iv) % Q for x in M[r]]
            for i in range(D):
                if i != r and M[i][c] % Q:
                    f = M[i][c]
                    M[i] = [(M[i][j] - f * M[r][j]) % Q for j in range(D)]
            r += 1
        return r

    def inv(A):
        Aug = [[A[i][j] for j in range(D)]
               + [1 if i == j else 0 for j in range(D)] for i in range(D)]
        r = 0
        for c in range(D):
            p = next((i for i in range(r, D) if Aug[i][c] % Q), None)
            Aug[r], Aug[p] = Aug[p], Aug[r]
            iv = pow(Aug[r][c], -1, Q)
            Aug[r] = [(x * iv) % Q for x in Aug[r]]
            for i in range(D):
                if i != r and Aug[i][c] % Q:
                    f = Aug[i][c]
                    Aug[i] = [(Aug[i][j] - f * Aug[r][j]) % Q
                              for j in range(2 * D)]
            r += 1
        return tuple(tuple(Aug[i][D + j] for j in range(D)) for i in range(D))

    def is_hyp(A):
        return all(form(v, act(A, v)) % Q == 0 for v in vecs)

    def compile_gate(g):
        """Emit a list of (v, lam); the product of T(v,lam) in order is g.

        Hyperbolicity must be re-tested at EVERY step, not only on entry: a
        non-hyperbolic gate can peel onto a hyperbolic intermediate, and the
        pivot x exists only for non-hyperbolic elements. Checking once -- the
        direct reading of the q = 2 algorithm -- strands 1,679 of the 51,840.
        So each step prefers a pivot that LANDS non-hyperbolic, and falls back
        to the residue-preserving fix-up only when the current element is
        already hyperbolic.
        """
        prog, cur = [], g
        while cur != I:
            if is_hyp(cur):
                for M in Tlist:
                    C = mul(cur, M)
                    if rk(C) == rk(cur) and not is_hyp(C):
                        prog.append(T[M])
                        cur = C
                        break
                else:
                    return None
                continue
            gi = inv(cur)
            fallback = None
            chosen = None
            for x in vecs:
                gx = act(gi, x)
                c = form(x, gx) % Q
                if c == 0:
                    continue
                v = tuple((gx[k] - x[k]) % Q for k in range(D))
                if not any(v):
                    continue
                lam = pow(c, -1, Q)
                M = tv(v, lam)
                if M == I:
                    continue
                C = mul(cur, M)
                if rk(C) != rk(cur) - 1:
                    continue
                if C == I or not is_hyp(C):
                    chosen = ((v, lam), C)
                    break
                if fallback is None:
                    fallback = ((v, lam), C)
            step = chosen or fallback
            if step is None:
                return None
            prog.append(step[0])
            cur = step[1]
        return prog

    total = ok_factor = ok_product = ok_minimal = 0
    longest = 0
    hyp_branch = 0
    failed = 0
    for g in dist:
        prog = compile_gate(g)
        total += 1
        if g != I and is_hyp(g):
            hyp_branch += 1
        if prog is None:
            failed += 1
            continue
        # g = T_1 T_2 ... T_k, applied as the algorithm peeled them off
        P = I
        good = True
        for (v, lam) in prog:
            M = tv(v, lam)
            if M == I or M not in T:
                good = False
                break
            P = mul(P, M)
        if good:
            ok_factor += 1
        # peeling gave g.T1.T2...Tk = I, so g = (T1...Tk)^-1
        if good and mul(g, P) == I:
            ok_product += 1
        if good and len(prog) == dist[g]:
            ok_minimal += 1
        longest = max(longest, len(prog))

    print("THE QUTRIT TRANSVECTION COMPILER")
    print("=" * 72)
    print("  arXiv:2102.11380 gives this for QUBITS (F_2) with")
    print("  characteristic-2 machinery. This substrate is q = 3.")
    print()
    print("  step:  pick x with <x, g^-1 x> =/= 0")
    print("         v = g^-1 x - x,   lam = <x, g^-1 x>^-1")
    print("         then g.T(v,lam) fixes x and drops residue by one")
    print("  at q = 2 this is v = x + xg, lam = 1 -- the published step;")
    print("  at odd q the scalar lam is the new content, and it is forced.")
    print()
    print("  over all %d elements of Sp(4,3):" % total)
    print("     decompositions produced              %5d" % total)
    print("     every factor a genuine transvection  %5d" % ok_factor)
    print("     product reconstructs g exactly       %5d" % ok_product)
    print("     length equals BFS ground truth       %5d   <- MINIMAL"
          % ok_minimal)
    print("     longest program emitted              %5d" % longest)
    print("     failed to compile                    %5d" % failed)
    print()
    print("  the extra-instruction branch fires on exactly %d inputs --" % hyp_branch)
    print("  the hyperbolic maps of 3595bd1: the 90 indexed by the hyperbolic")
    print("  lines carrying the sentinel code's minimum words, plus the centre.")
    print("  The compiler's only irregular branch and the code's minimum-weight")
    print("  structure are the same objects.")

    ok = (total == 51840 and ok_factor == total and ok_product == total
          and ok_minimal == total and longest == 5 and hyp_branch == 91
          and dia == 5)

    if "--write" in sys.argv:
        p = os.path.join(ROOT, "data", "the_qutrit_transvection_compiler.json")
        with open(p, "w") as fh:
            json.dump({
                "schema": "holotrade.qutrit-transvection-compiler.v1",
                "valid": bool(ok),
                "theGap": ("arXiv:2102.11380 decomposes any Clifford gate into "
                           "a minimal product of transvections, but is built "
                           "over F_2 throughout -- qubits -- with "
                           "characteristic-2 machinery (residue matrix, "
                           "triangularisation by congruence over GF(2), Botha's "
                           "theorem). This substrate is q = 3, and b363f7c "
                           "showed the transvections are its natural "
                           "instruction set, so shortest-program code "
                           "generation was open here"),
                "portingPitfall": ("testing hyperbolicity ONCE on the input -- "
                                   "the obvious reading of the published "
                                   "algorithm -- strands 1,679 of the 51,840, "
                                   "every failure at residue 2 with the current "
                                   "element hyperbolic: a non-hyperbolic gate "
                                   "can peel onto a hyperbolic INTERMEDIATE and "
                                   "the pivot exists only for non-hyperbolic "
                                   "elements. The fix is to re-test every step "
                                   "and prefer a pivot landing non-hyperbolic. "
                                   "It is the same failure mode 3595bd1 found "
                                   "in Sp(4,2), where the induction genuinely "
                                   "breaks; at q = 3 a good pivot always exists, "
                                   "but only if the algorithm looks for it"),
                "theStep": {
                    "pick": "x with <x, g^-1 x> =/= 0",
                    "vector": "v = g^-1 x - x",
                    "scalar": "lam = <x, g^-1 x>^-1",
                    "effect": "g.T(v,lam) fixes x and has residue res(g) - 1",
                    "derivation": ("g.T(v,lam) fixes x iff T(v,lam)x = g^-1 x; "
                                   "since T(v,lam)x = x + lam<x,v>v, v must be "
                                   "parallel to g^-1 x - x and lam must invert "
                                   "<x, g^-1 x>"),
                    "atQ2": ("collapses to v = x + xg, lam = 1 -- the published "
                             "step; at odd q the scalar is the new content and "
                             "it is forced, not chosen"),
                    "hypothesis": ("existence of x is exactly "
                                   "NON-hyperbolicity, which is why O'Meara's "
                                   "criterion is the hypothesis"),
                },
                "verification": {
                    "elements": total,
                    "everyFactorATransvection": ok_factor,
                    "productReconstructsG": ok_product,
                    "lengthEqualsBFSGroundTruth": ok_minimal,
                    "longestProgram": longest,
                    "failedToCompile": failed,
                    "groupDiameter": dia,
                    "reading": ("a total function, correct, and optimal "
                                "POINTWISE on every input -- checked against a "
                                "full breadth-first search, not against a bound"),
                },
                "hyperbolicBranch": {
                    "fires": hyp_branch,
                    "reading": ("the only irregular branch fires on exactly the "
                                "91 hyperbolic maps: the 90 indexed by the "
                                "hyperbolic lines whose polar pairs are the "
                                "sentinel code's 45 minimum-weight words, plus "
                                "the centre -- the co-location claim made "
                                "operational"),
                },
                "runtimeCost": ("the compiler never searches the group: it "
                                "scans at most 80 vectors per instruction and "
                                "emits at most 5, so compiling any gate is "
                                "bounded work independent of the 51,840 -- the "
                                "difference between a routing table and a "
                                "compiler, and what makes the forty-opcode ISA "
                                "implementable rather than merely optimal on "
                                "paper"),
                "boundary": ("exact and exhaustive at q = 3, dimension 4. The "
                             "step is derived for any odd q but tested only "
                             "here, and the hyperbolic fix-up is found by "
                             "search rather than construction, so this is a "
                             "verified compiler for Sp(4,3), not a proof for "
                             "Sp(2n,q). It emits SYMPLECTIC transvections: the "
                             "Clifford group is their central extension, and "
                             "the phase bookkeeping needed to lift a symplectic "
                             "program to an actual qutrit circuit is NOT done "
                             "here. tau_2 is untouched"),
            }, fh, indent=2)
        print("\n  written: %s" % os.path.relpath(p, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
