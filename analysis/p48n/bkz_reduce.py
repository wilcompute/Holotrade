import sys
from fpylll import IntegerMatrix, GSO, LLL, BKZ
from fpylll.fplll.bkz_param import BKZParam
from screen_fpylll import read_gram

ss = int(sys.argv[1])
G = read_gram("/mnt/c/tools/pari/cands/G%d.txt" % ss)
n = len(G)
A = IntegerMatrix.from_matrix(G)
U = IntegerMatrix.identity(n)
M = GSO.Mat(A, U=U, gram=True)
M.update_gso()
L = LLL.Reduction(M)
L()
for bs in (20, 30):
    B = BKZ.Reduction(M, L, BKZParam(block_size=bs, flags=BKZ.AUTO_ABORT))
    B()
M.update_gso()
rows = [[U[i, j] for j in range(n)] for i in range(n)]
with open("/mnt/c/tools/pari/p48n_U.gp", "w") as fh:
    fh.write("UB = [" + ";".join(",".join(str(v) for v in r) for r in rows) + "];\n")
print("GS log-norms (first, last):", M.get_r(0, 0), M.get_r(n - 1, n - 1))
