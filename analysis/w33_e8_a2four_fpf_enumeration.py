"""Independent enumeration: every fixed-point-free order-3 element from A2^4 subsystems.

By Carter's classification an order-3 element of W(E8) has type A2, 2A2, 3A2 or 4A2, and only
4A2 is fixed-point-free (the others fix a subspace of dimension 6, 4, 2).  A 4A2 element is a
product of Coxeter rotations of four mutually orthogonal A2 subsystems.  So enumerating the
A2^4 subsystems and their sign choices enumerates the fixed-point-free order-3 elements by a
route completely independent of the conjugacy-orbit computation.  If the two agree, the orbit
is the whole set and the class is unique.
"""
import itertools
import json
from fractions import Fraction

exec(open('canonical.py').read().split('def main()')[0])   # reuse roots / ip / matmul / ...

def main():
    R = e8_roots()
    S = simple_roots(R)
    C = [[ip(S[i], S[j]) for j in range(8)] for i in range(8)]

    # coordinates of every root in the simple-root basis (exact)
    Smat = [[S[j][k] for j in range(8)] for k in range(8)]
    def solve(rv):
        A = [[Fraction(Smat[i][j]) for j in range(8)] + [Fraction(rv[i])] for i in range(8)]
        for col in range(8):
            piv = next(r for r in range(col, 8) if A[r][col] != 0)
            A[col], A[piv] = A[piv], A[col]
            pv = A[col][col]
            A[col] = [v / pv for v in A[col]]
            for r in range(8):
                if r != col and A[r][col] != 0:
                    f = A[r][col]
                    A[r] = [a - f * b for a, b in zip(A[r], A[col])]
        return tuple(int(A[i][8]) for i in range(8))
    basis = {r: solve(r) for r in R}

    # ---- A2 subsystems: {+-a, +-b, +-(a+b)} for (a,b) = -1
    A2 = set()
    Rset = set(R)
    for a in R:
        for b in R:
            if ip(a, b) == -1:
                c = tuple(x + y for x, y in zip(a, b))
                if c in Rset:
                    A2.add(frozenset([a, b, c, tuple(-x for x in a),
                                      tuple(-x for x in b), tuple(-x for x in c)]))
    A2 = sorted(A2, key=lambda s: sorted(s))
    print("A2 subsystems in E8            :", len(A2))

    # ---- orthogonality graph between A2s
    span = [sorted(s) for s in A2]
    n = len(A2)
    orth = [set() for _ in range(n)]
    for i in range(n):
        ri = span[i]
        for j in range(i + 1, n):
            if all(ip(x, y) == 0 for x in ri for y in span[j]):
                orth[i].add(j)
                orth[j].add(i)
    print("mean orthogonal partners       : %.1f" % (sum(len(o) for o in orth) / n))

    # ---- 4-cliques = A2^4 subsystems
    quads = []
    for i in range(n):
        Ni = {j for j in orth[i] if j > i}
        for j in sorted(Ni):
            Nj = Ni & orth[j]
            for k in sorted(x for x in Nj if x > j):
                Nk = Nj & orth[k]
                for l in sorted(x for x in Nk if x > k):
                    quads.append((i, j, k, l))
    print("A2^4 subsystems                :", len(quads))

    # ---- rotation of an A2 in the simple-root basis
    def refl(r):
        """reflection in root r, as a matrix in the simple-root basis"""
        M = []
        for j in range(8):
            aj = S[j]
            v = tuple(x - ip(aj, r) * y for x, y in zip(aj, r))
            M.append(basis[v])
        # columns are images of basis vectors
        return tuple(tuple(M[j][i] for j in range(8)) for i in range(8))

    def rot(a2):
        """order-3 rotation of the A2: product of two reflections in non-opposite roots"""
        rs = sorted(a2)
        a = rs[0]
        b = next(x for x in rs if ip(a, x) == -1)
        return matmul(refl(a), refl(b))

    rots = {}
    fpf = set()
    for q in quads:
        mats = []
        for idx in q:
            if idx not in rots:
                rots[idx] = rot(A2[idx])
            mats.append(rots[idx])
        for signs in itertools.product((1, 2), repeat=4):
            M = identity()
            for m, s in zip(mats, signs):
                p = m if s == 1 else matmul(m, m)
                M = matmul(M, p)
            fpf.add(M)
    print("distinct products               :", len(fpf))

    # verify each is fixed-point-free of order 3
    ok = sum(1 for M in fpf
             if matmul(M, matmul(M, M)) == identity() and sum(charpoly_int(M)) != 0)
    print("  of which fpf of order 3       :", ok)

    out = {"A2_subsystems": len(A2), "A2_4_subsystems": len(quads),
           "distinct_fpf_elements": len(fpf), "all_fpf_order3": ok == len(fpf),
           "sixteen_per_quad": len(quads) * 16,
           "matches_class_size": len(fpf) == 4480}
    json.dump(out, open("a2four.json", "w"), indent=1)
    print()
    print("16 x (A2^4 subsystems)          :", len(quads) * 16)
    print("distinct fpf order-3 elements   :", len(fpf))
    print("conjugacy class size from orbit : 4480")
    print("AGREE                           :", len(fpf) == 4480)

if __name__ == "__main__":
    main()
