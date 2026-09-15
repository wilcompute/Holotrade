default(parisizemax, 8*10^9);
default(nbthreads, 12);
read("C:/tools/pari/p48_units.gp");
m = 65; n = 48;
f = polcyclo(m, x);
z = Mod(x, f);
\\ generator of the different of Z[zeta_65]: (1-z5)^3 (1-z13)^11, z5 = z^13, z13 = z^5
gam = (1 - z^13)^3 * (1 - z^5)^11;
\\ find a root of unity e with e*gam real (fixed by x -> x^-1)
conjm(a) = Mod(subst(lift(a), x, x^(m - 1)), f);
eps = 0;
for (k = 0, 2*m - 1, e = (-1)^k * z^(k % m); if (conjm(e * gam) == e * gam, eps = e; break));
if (eps == 0, error("no real twist"));
beta = 1 / (eps * gam);
print("beta real: ", conjm(beta) == beta);
\\ real embeddings of K+: evaluate at zeta^j, j = 1..32 coprime to 65 up to sign
J = select(j -> gcd(j, m) == 1, [1..32]);
print("#real embeddings ", #J);
emb(a) = vector(#J, t, real(subst(lift(a), x, exp(2*Pi*I*J[t]/m))));
sgn(a) = apply(v -> if (v > 0, 1, -1), emb(a));
\\ units of K+ lifted to K
U = concat([Mod(-1, f)], apply(u -> Mod(subst(u, y, x + x^(m - 1)), f), FU));
SG = vector(#U, c, sgn(U[c])); SU = matrix(#J, #U, r, c, (1 - SG[c][r]) / 2);
\\ make beta totally positive: solve SU * c = signs(beta) over F2
SB = sgn(beta); sb = vectorv(#J, r, (1 - SB[r]) / 2);
sol = matsolvemod(SU, 2, sb);
if (type(sol) == "t_INT", error("beta signs not in unit sign image"));
e0 = prod(i = 1, #U, U[i]^(sol[i] % 2));
alpha0 = beta / e0;
print("alpha0 totally positive: ", vecmin(emb(alpha0)) > 0);
\\ totally positive units mod squares: F2-kernel of SU
Kk = matker(Mod(SU, 2));
print("kernel dim ", #Kk);
tp = vector(#Kk, i, prod(j = 1, #U, U[j]^(lift(Kk[j, i]))));
T0 = vector(m, k, my(g = gcd(k - 1, m)); moebius(m / g) * eulerphi(m) / eulerphi(m / g));
lintr(a, sh) = my(c = Vecrev(Vec(lift(a)))); sum(i = 1, #c, c[i] * T0[((i - 1 + sh) % m) + 1]);
{ for (ss = 0, 31, my(u = prod(i = 1, #Kk, tp[i]^bittest(ss, i - 1)), A = alpha0 * u, T, G); T = vector(2*n - 1, k, lintr(A, (k - n) % m)); G = matrix(n, n, i, j, T[i - j + n]); write("C:/tools/pari/cands/G" ss ".txt", Str(G)); write("C:/tools/pari/cands/A" ss ".txt", Str(lift(A)))); }
quit;
