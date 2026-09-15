default(parisizemax, 8*10^9);
G48 = eval(readstr("C:/tools/pari/cands/G25.txt")[1]); read("C:/tools/pari/p48n_U.gp");
m = 65; n = 48; p = 13;
f = polcyclo(m, x);
\\ sigma = multiplication by zeta^5 (order 13) on the power basis 1, z, ..., z^47 (column convention)
Ms = matrix(n, n, i, j, polcoeff(lift(Mod(x^(j - 1 + 5), f)), i - 1));
print("sigma preserves G: ", Ms~ * G48 * Ms == G48);
S13 = sum(k = 0, 12, Ms^k);
print("Phi_13(sigma) = 0: ", S13 == 0);
L = UB~; G2 = L~ * G48 * L; Li = L^-1; print("unimodular transform: ", abs(matdet(L)) == 1);
s2 = Li * Ms * L;
print("det G = ", matdet(G48), ", min diag after LLL ", vecmin(vector(n, i, G2[i, i])));
lam = [-462, -1, 330, 11, -165, -55, 55, 165, -11, -330, 1, 462, 0];
Wm = G2 * sum(k = 0, 12, lam[k + 1] * s2^k);
B(u, v) = (u~ * Wm * v) % p;
\\ choose 4 short vectors with nondegenerate Gram mod 13
sv = qfminim(G2, 6, 400, 2)[3];
{
basis = 0;
for (t = 1, 5000,
  my(idx = vector(4, i, random(#sv) + 1), bb = vector(4, i, sv[, idx[i]]), Gm = matrix(4, 4, i, j, B(bb[i], bb[j])));
  if (matrank(Mod(Gm, p)) == 4, basis = bb; GR = Gm; break));
}
print("Gram mod 13: ", GR);
print("alternating: ", Mod(GR + GR~, p) == 0 && vecmax(abs(vector(4, i, GR[i, i]))) == 0);
\\ well defined on L/pi L: B((1 - sigma) u, v) = 0
print("well-defined on L/piL: ", B((matid(n) - s2) * sv[, 1], sv[, 2]) == 0 && B((matid(n) - s2) * sv[, 3], sv[, 7]) == 0);
GI = lift(Mod(GR, p)^-1);
Wb = vector(4, j, Wm * basis[j]);
cnt = vector(p^4, i, 0);
tot = 0; t0 = getabstime();
{
forqfvec(v, G2, 6,
  my(P = vector(4, j, (v~ * Wb[j]) % p), c = (P * GI) % p, key, keyn);
  key = c[1] + p * c[2] + p^2 * c[3] + p^3 * c[4];
  keyn = ((-c[1]) % p) + p * ((-c[2]) % p) + p^2 * ((-c[3]) % p) + p^3 * ((-c[4]) % p);
  cnt[key + 1]++; cnt[keyn + 1]++; tot += 2;
  if (tot % 4000000 == 0, print("  ", tot, " vectors, ", (getabstime() - t0) \ 1000, " s")));
}
print("total minimal vectors (norm 6): ", tot);
print("zero class: ", cnt[1]);
write("C:/tools/pari/p48n_counts25.gp", "CNT = ", cnt, ";");
write("C:/tools/pari/p48n_counts25.gp", "GR = ", GR, ";");
h = Map();
for (i = 2, p^4, my(c = cnt[i]); if (mapisdefined(h, c), mapput(h, c, mapget(h, c) + 1), mapput(h, c, 1)));
print("count histogram over nonzero classes: ", Mat(h));
quit;
