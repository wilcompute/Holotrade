#!/usr/bin/env python3
"""Run the exact 111-leaf lift with general nonnegative integer tile excess.

The first leaf-lift implementation accidentally specialized the frozen
factorization to binary excess E.  The factorization theorem never asserted
that: E=U N^T=N V may contain entries 2 or larger.  This wrapper patches only
that false diagnostic assumption and delegates the exact local-state/leaf CSP,
independent reconstruction, and scope discipline to
``the_111_factorization_leaf_lift.py``.

For every frozen factorization we require exactly:
  * E from row tokens equals E from column tokens entrywise;
  * E is nonnegative integer with total excess 176;
  * T=J+E has total tile occupancy 1776=16*111.
No occupancy upper bound is imposed.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis" / "the_111_factorization_leaf_lift.py"

spec = importlib.util.spec_from_file_location("leaf_lift_v1", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import original exact leaf lift")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def target_occupancy_general(row_tokens, col_tokens, N):
    E1 = [[sum(N[j][p] for p in row_tokens[i]) for j in range(40)]
          for i in range(40)]
    E2 = [[sum(N[i][p] for p in col_tokens[j]) for j in range(40)]
          for i in range(40)]
    assert E1 == E2
    flat = [x for row in E1 for x in row]
    assert all(type(x) is int and x >= 0 for x in flat)
    assert sum(flat) == 176
    T = [[1 + E1[i][j] for j in range(40)] for i in range(40)]
    assert sum(sum(row) for row in T) == 16 * 111 == 1776
    return T


mod.target_occupancy = target_occupancy_general

if __name__ == "__main__":
    mod.main()
