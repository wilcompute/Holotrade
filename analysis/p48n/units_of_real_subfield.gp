default(parisizemax, 4*10^9);
default(nbthreads, 12);
m = 65;
f = polcyclo(m, x);
\\ real subfield K+ = Q(z + 1/z)
g = polsubcyclo(m, 24);
print("candidates for degree-24 subfields: ", #g);
t0 = getabstime();
\\ the maximal real subfield: minimal polynomial of z + 1/z
K = nfinit(f);
r = Mod(x + x^(-1) , f);
pr = minpoly(r, y);
print("minpoly degree ", poldegree(pr));
Kp = bnfinit(pr, 1);
print("bnfinit K+ time ", getabstime() - t0, " ms; class number ", Kp.no, "; unit rank ", #Kp.fu);
print("signature ", Kp.sign);
\\ signs of fundamental units at the real embeddings
S = matrix(24, #Kp.fu + 1);
for (j = 1, 24, S[j, 1] = -1);
for (i = 1, #Kp.fu, u = nfbasistoalg(Kp, Kp.fu[i]); v = nfeltsign(Kp, u); for (j = 1, 24, S[j, i + 1] = v[j]));
\\ rank over F2 of the sign map (with -1)
M2 = matrix(24, #Kp.fu + 1, j, i, (1 - S[j, i]) / 2);
print("F2-rank of sign map on units (incl. -1): ", matrank(Mod(M2, 2)));
write("C:/tools/pari/p48_units.gp", "KPPOL = ", pr, ";");
write("C:/tools/pari/p48_units.gp", "FU = ", apply(u -> lift(nfbasistoalg(Kp, u)), Kp.fu), ";");
quit;
