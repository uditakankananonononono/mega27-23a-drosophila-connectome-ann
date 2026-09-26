"""Fast exact 16-class triad census for large hub-heavy digraphs.

Method: every quantity below is linear in the triad-class counts. The linear
map from class counts -> quantities is constructed EXACTLY by evaluating the
quantities on one canonical 3-node representative of each MAN class
(representatives selected by networkx.triad_type over all 64 edge patterns,
no hand-derived conventions). census = lstsq(M, q), rounded to int.

Validated against igraph.triad_census on random + structured digraphs in
tests/test_fast_census.py. Statistics identical to PREREGISTRATION lock;
this is an implementation swap only.
"""
import os
from fractions import Fraction
import numpy as np
import scipy.sparse as sp

TRIAD_LABELS = ["003","012","102","021D","021U","021C","111D","111U",
                "030T","030C","201","120D","120U","120C","210","300"]




def _blocked_masked_sums2(L, R, masks, block=4000):
    """Return [sum((L@R) . M) for M in masks] without materializing L@R."""
    n = L.shape[0]
    Rcsc = R.tocsc()
    Mcsc = [M.tocsc() for M in masks]
    acc = [0] * len(masks)
    for s in range(0, n, block):
        J = slice(s, min(s + block, n))
        C = L @ Rcsc[:, J]
        for k, M in enumerate(Mcsc):
            acc[k] += int(C.multiply(M[:, J]).sum())
    return acc

def _to_csr(g):
    edges = np.array(g.get_edgelist(), dtype=np.int64).reshape(-1, 2)
    n = g.vcount()
    A = sp.csr_matrix((np.ones(len(edges), dtype=np.int64), (edges[:, 0], edges[:, 1])),
                      shape=(n, n), dtype=np.int64)
    A.sum_duplicates()
    A.data[:] = 1
    A.setdiag(0)
    A.eliminate_zeros()
    return A


def _blocked_masked_sums(A, masks, block=4000):
    """Return [sum((A@A) . M) for M in masks] without materializing A@A."""
    n = A.shape[0]
    Acsc = A.tocsc()
    Mcsc = [M.tocsc() for M in masks]
    acc = [0] * len(masks)
    for s in range(0, n, block):
        J = slice(s, min(s + block, n))
        C = A @ Acsc[:, J]
        for k, M in enumerate(Mcsc):
            acc[k] += int(C.multiply(M[:, J]).sum())
    return acc


def quantities(A):
    """Linear-in-triad quantities of binary csr adjacency A (no self-loops)."""
    n = A.shape[0]
    At = A.T.tocsr()
    B = A.multiply(At).tocsr()          # mutual adjacency
    din = np.asarray(A.sum(axis=0)).ravel()
    dout = np.asarray(A.sum(axis=1)).ravel()
    dB = np.asarray(B.sum(axis=1)).ravel()
    dU = din + dout - dB                # |N+ union N-|
    E = int(A.sum())
    q = []
    q.append(n * (n - 1) * (n - 2) // 6)                 # q0 = C(n,3)
    q.append(E * (n - 2))                                # q1
    q.append(int(B.sum()) // 2 * (n - 2))                # q2 mutual*(n-2)
    q.append(int((dout * (dout - 1)).sum()) // 2)        # q3 out-2-stars
    q.append(int((din * (din - 1)).sum()) // 2)          # q4 in-2-stars
    q.append(int((dout * din).sum()) - int(dB.sum()))   # q5 mixed, 3-distinct-nodes only
    q.append(int((dB * (dB - 1)).sum()) // 2)            # q6 mutual 2-stars
    q.append(int((dB * dout).sum()) - int(dB.sum()))    # q7, 3-distinct only
    q.append(int((dB * din).sum()) - int(dB.sum()))     # q8, 3-distinct only
    q.append(int((dU * (dU - 1)).sum()) // 2)            # q9 undirected 2-stars
    q.append(int((dU * dB).sum()) - int(dB.sum()))      # q10, 3-distinct only
    # triangle products: for base products P in {A,At,B}x{A,At,B}, sums <P, M> for M in {A,At,B}
    masks = [A, At, B]
    for base_left, base_right in ((A, A), (At, At), (B, B), (B, A), (B, At), (A, B)):
        vals = _blocked_masked_sums2(base_left, base_right, masks)
        q.extend(vals)
    return np.array(q, dtype=np.int64)


_QCACHE = None

def _matrix():
    """Coefficient matrix M (quantities x 16 classes) from canonical reps."""
    global _QCACHE
    if _QCACHE is not None:
        return _QCACHE
    import itertools, networkx as nx
    reps = {}
    for bits in range(64):
        pairs = [(0,1),(1,0),(0,2),(2,0),(1,2),(2,1)]
        edges = [pairs[i] for i in range(6) if bits >> i & 1]
        G = nx.DiGraph(); G.add_nodes_from([0,1,2]); G.add_edges_from(edges)
        t = nx.triad_type(G)
        if t not in reps:
            reps[t] = edges
    assert set(reps) == set(TRIAD_LABELS), set(TRIAD_LABELS) - set(reps)
    cols = []
    for lab in TRIAD_LABELS:
        edges = reps[lab]
        A = sp.csr_matrix((np.ones(len(edges), dtype=np.int64),
                           ([e[0] for e in edges], [e[1] for e in edges])),
                          shape=(3, 3), dtype=np.int64) if edges else sp.csr_matrix((3, 3), dtype=np.int64)
        cols.append(quantities(A))
    M = np.stack(cols, axis=1)
    _QCACHE = M
    return M


_L_CACHE = None

def _left_inverse():
    """Exact rational left-inverse L (16 x 29) of the coefficient matrix,
    precomputed with sympy and verified L @ M == I. Makes the census solve
    EXACT integer arithmetic, immune to float conditioning on huge graphs."""
    global _L_CACHE
    if _L_CACHE is None:
        import json
        from fractions import Fraction
        path = os.path.join(os.path.dirname(__file__), "census_left_inverse.json")
        rows = json.load(open(path))
        _L_CACHE = [[Fraction(x) for x in row] for row in rows]
    return _L_CACHE


def census(A):
    """A: binary csr adjacency, no self-loops. Returns dict label -> int count (EXACT)."""
    q = quantities(A).astype(np.int64).tolist()
    L = _left_inverse()
    c = []
    for row in L:
        acc = Fraction(0)
        for lij, qj in zip(row, q):
            if lij:
                acc += lij * qj
        assert acc.denominator == 1, f"non-integer census value {acc}"
        c.append(int(acc))
    return dict(zip(TRIAD_LABELS, c))


def census_igraph(g):
    return census(_to_csr(g))
