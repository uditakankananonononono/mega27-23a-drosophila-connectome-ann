"""Null convergence diagnostic (AMENDMENT-4, judge round 2 critique A).
Question: does the DP swap chain reach an approximately stationary null by
10 swaps/edge? Method: continue one chain to 20 swaps/edge, snapshotting the
edge set at 0,1E,2E,5E,10E,20E successful swaps; compute the 16-class census
at each snapshot; report per-class relative change between 10E and 20E.
Convergence criterion (locked): |count(20E)-count(10E)|/|count(20E)| < 0.02
for every class with count(20E) >= 100 (small-count classes reported but
exempt). If violated, swaps/edge for N1 must increase (new amendment).
"""
import numpy as np
import scipy.sparse as sp
import fast_census, nulls

def census_at(pre, post, n):
    A = sp.csr_matrix((np.ones(len(pre), dtype=np.int64), (pre, post)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    return fast_census.census(A)

def run_chain(pre, post, n, seed, fractions=(0, 1, 2, 5, 10, 20)):
    """Rewire incrementally, snapshotting at each fraction x E swaps."""
    E = len(pre)
    p, q = pre.copy(), post.copy()
    out = {}
    done = 0
    for f in fractions:
        target = int(f * E)
        if target > done:
            p, q = nulls.dp_rewire_np(p, q, n, target - done, seed + done)
            done = target
        out[f] = census_at(p, q, n)
    return out

def plateau_report(out):
    a, b = out[10], out[20]
    rows = {}
    ok = True
    for k in a:
        if b[k] >= 100:
            rel = abs(b[k] - a[k]) / max(abs(b[k]), 1)
            rows[k] = rel
            ok &= rel < 0.02
        else:
            rows[k] = None
    return rows, ok
