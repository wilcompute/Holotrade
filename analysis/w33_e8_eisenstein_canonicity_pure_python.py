"""Is the Eisenstein structure on E8 unique up to Aut(E8)?

The program rests on E8 -> W(3,3) via a fixed-point-free order-3 automorphism rho (= c^10,
c a Coxeter element).  PASS7385-7400 built that bridge explicitly.  What was never asked is
whether rho is CANONICAL: if W(E8) had several conjugacy classes of fixed-point-free order-3
elements, each would give a different Z[omega]-structure and a different mod-theta reduction,
and W(3,3) would be a choice rather than a consequence.

Everything below is exact integer arithmetic in the simple-root basis, where W(E8) sits in
GL_8(Z).  No floating point enters the group theory.
"""
import itertools
import json
from fractions import Fraction

# ---------------------------------------------------------------- E8 roots (doubled coords)
def e8_roots():
    """240 roots, stored as 2*r so every entry is an integer.  (r,s) = dot(2r,2s)/4."""
    R = []
    for i in range(8):
        for j in range(i + 1, 8):
            for si in (2, -2):
                for sj in (2, -2):
                    v = [0] * 8
                    v[i] = si
                    v[j] = sj
                    R.append(tuple(v))
    for signs in itertools.product((1, -1), repeat=8):
        if signs.count(-1) % 2 == 0:
            R.append(tuple(signs))
    return R

def ip(a, b):
    """Inner product with roots normalised to norm 2."""
    s = sum(x * y for x, y in zip(a, b))
    assert s % 4 == 0
    return s // 4

# ---------------------------------------------------------------- simple roots + Cartan
def simple_roots(R):
    f = [1, 3, 9, 27, 81, 243, 729, 2188]          # generic functional, no root on the wall
    pos = [r for r in R if sum(c * x for c, x in zip(f, r)) > 0]
    assert len(pos) == 120
    posset = set(pos)
    simple = []
    for r in pos:
        decomposable = False
        for a in pos:
            b = tuple(x - y for x, y in zip(r, a))
            if b in posset:
                decomposable = True
                break
        if not decomposable:
            simple.append(r)
    assert len(simple) == 8, len(simple)
    return simple

def matmul(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(8)) for j in range(8))
                 for i in range(8))

def identity():
    return tuple(tuple(1 if i == j else 0 for j in range(8)) for i in range(8))

def charpoly_int(M):
    """Exact characteristic polynomial via Faddeev-LeVerrier over Fractions."""
    n = 8
    A = [[Fraction(M[i][j]) for j in range(n)] for i in range(n)]
    I = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
    Mk = [[Fraction(0)] * n for _ in range(n)]
    coeffs = [Fraction(1)]
    for k in range(1, n + 1):
        # Mk = A*Mk + c_{k-1} I
        AM = [[sum(A[i][t] * Mk[t][j] for t in range(n)) for j in range(n)] for i in range(n)]
        for i in range(n):
            AM[i][i] += coeffs[-1]
        Mk = AM
        AMk = [[sum(A[i][t] * Mk[t][j] for t in range(n)) for j in range(n)] for i in range(n)]
        c = -Fraction(sum(AMk[i][i] for i in range(n)), k)
        coeffs.append(c)
    return [int(c) for c in coeffs]          # leading first

def main():
    R = e8_roots()
    assert len(R) == 240
    S = simple_roots(R)
    C = [[ip(S[i], S[j]) for j in range(8)] for i in range(8)]
    assert all(C[i][i] == 2 for i in range(8))

    # simple reflections in the simple-root basis: s_i(a_j) = a_j - C_ij a_i
    gens = []
    for i in range(8):
        M = [[1 if k == j else 0 for j in range(8)] for k in range(8)]
        for j in range(8):
            M[i][j] -= C[i][j]
        gens.append(tuple(tuple(row) for row in M))

    # Coxeter element and rho = c^10
    c = identity()
    for g in gens:
        c = matmul(c, g)
    # order of c
    p, order_c = c, 1
    while p != identity():
        p = matmul(p, c)
        order_c += 1
    rho = identity()
    for _ in range(10):
        rho = matmul(rho, c)

    cp = charpoly_int(rho)
    # (x^2+x+1)^4 expanded
    target = [1, 4, 10, 16, 19, 16, 10, 4, 1]
    rho3 = matmul(rho, matmul(rho, rho))
    # fixed vectors: det(rho - I) != 0
    dm = [[rho[i][j] - (1 if i == j else 0) for j in range(8)] for i in range(8)]
    detpoly = charpoly_int(rho)          # char poly at 1 gives det(I*1 - rho) up to sign
    det_rho_minus_I = sum(detpoly)       # p(1) = det(I - rho)

    print("Coxeter element order          :", order_c)
    print("rho^3 == I                     :", rho3 == identity())
    print("char poly of rho               :", cp)
    print("  equals (x^2+x+1)^4           :", cp == target)
    print("det(I - rho) (0 => fixed vector):", det_rho_minus_I)
    print("fixed-point-free                :", det_rho_minus_I != 0)

    # --------------------------------------------------- conjugacy orbit of rho in W(E8)
    seen = {rho}
    frontier = [rho]
    while frontier:
        nxt = []
        for x in frontier:
            for g in gens:
                gi = tuple(tuple(r) for r in g)       # reflections are involutions: g^-1 = g
                y = matmul(gi, matmul(x, g))
                if y not in seen:
                    seen.add(y)
                    nxt.append(y)
        frontier = nxt
    orbit = len(seen)
    WE8 = 696729600
    print()
    print("conjugacy class size of rho    :", orbit)
    print("|W(E8)| / class size           :", Fraction(WE8, orbit))
    print("  == 155520 (|Z3 x Sp(4,3)|)   :", WE8 // orbit == 155520 and WE8 % orbit == 0)

    # every element of the class is fixed-point-free of order 3 (sanity)
    bad = 0
    for x in list(seen)[:400]:
        if matmul(x, matmul(x, x)) != identity() or sum(charpoly_int(x)) == 0:
            bad += 1
    print("sampled class members fpf ord-3:", 400 - bad, "of 400")

    # --------------------------------------------------- control: 240 roots -> 40 orbits
    # act on roots in the simple-root basis
    coord = {}
    Smat = [[S[j][k] for j in range(8)] for k in range(8)]   # columns = simple roots
    # express each root in simple-root basis by solving Smat * x = r  (exact, via Fractions)
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
    rb = [solve(r) for r in R]
    def act(M, v):
        return tuple(sum(M[i][j] * v[j] for j in range(8)) for i in range(8))
    unseen = set(rb)
    orbits = []
    while unseen:
        v = next(iter(unseen))
        o = set()
        for k in range(3):
            w = v
            for _ in range(k):
                w = act(rho, w)
            o.add(w)
            o.add(tuple(-x for x in w))
        orbits.append(o)
        unseen -= o
    print()
    print("root orbits under <-1, rho>    :", len(orbits))
    print("  all of size 6                :", all(len(o) == 6 for o in orbits))
    print("  240 = 6 x 40                 :", len(orbits) * 6 == 240)

    out = {"coxeter_order": order_c, "rho_order_3": rho3 == identity(),
           "charpoly": cp, "charpoly_is_phi3_4": cp == target,
           "det_I_minus_rho": det_rho_minus_I, "fixed_point_free": det_rho_minus_I != 0,
           "class_size": orbit, "WE8": WE8,
           "centralizer_order": WE8 // orbit if orbit and WE8 % orbit == 0 else None,
           "centralizer_is_155520": (WE8 % orbit == 0 and WE8 // orbit == 155520),
           "root_orbits": len(orbits), "all_orbits_size_6": all(len(o) == 6 for o in orbits)}
    json.dump(out, open("canonical.json", "w"), indent=1)
    print("\nwritten canonical.json")

if __name__ == "__main__":
    main()
