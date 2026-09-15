import sys, time, re
from fpylll import IntegerMatrix, GSO, LLL, BKZ, Enumeration, EnumerationError
from fpylll.fplll.bkz_param import BKZParam

def read_gram(path):
    s = open(path).read().strip()
    rows = s.strip("[]").split(";")
    return [[int(v) for v in r.split(",")] for r in rows]

def count_short(G, radius2, bkz=20):
    n = len(G)
    A = IntegerMatrix.from_matrix(G)
    M = GSO.Mat(A, gram=True)
    M.update_gso()
    L = LLL.Reduction(M)
    L()
    B = BKZ.Reduction(M, L, BKZParam(block_size=bkz, flags=BKZ.AUTO_ABORT))
    B()
    M.update_gso()
    E = Enumeration(M, nr_solutions=10**7)
    try:
        sols = E.enumerate(0, n, radius2 + 0.5, 0)
    except EnumerationError:
        return 0
    return len(sols)

if __name__ == "__main__":
    for ss in range(int(sys.argv[1]), int(sys.argv[2])):
        G = read_gram("/mnt/c/tools/pari/cands/G%d.txt" % ss)
        t = time.time()
        c2 = count_short(G, 2)
        c4 = count_short(G, 4)
        print("candidate %d: vectors with norm <= 2: %d, <= 4: %d  (%.1fs)" % (ss, c2, c4, time.time() - t), flush=True)
