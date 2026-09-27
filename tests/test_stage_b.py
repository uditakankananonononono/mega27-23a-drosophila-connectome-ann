import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
import stage_b
import pyarrow.feather as pf
import pyarrow as pa

def _write(tmp, name, idcol, rows):
    t = pa.table({idcol: [r[0] for r in rows], "neuropil": [r[1] for r in rows], "count": [r[2] for r in rows]})
    path = os.path.join(tmp, name)
    pf.write_feather(t, path)
    return path

def test_assign_primary_neuropil(tmp_path):
    pre = _write(tmp_path, "pre.feather", "pre_pt_root_id", [(1, "MB", 10), (1, "LH", 5), (2, "LH", 7)])
    post = _write(tmp_path, "post.feather", "post_pt_root_id", [(1, "MB", 3), (1, "LH", 9), (2, "LH", 1), (3, "CX", 4)])
    a = stage_b.assign_primary_neuropil(pre, post).set_index("root_id")
    assert a.loc[1, "primary_neuropil"] == "LH"   # 5+9=14 beats 10+3=13
    assert a.loc[2, "primary_neuropil"] == "LH"
    assert a.loc[3, "primary_neuropil"] == "CX"
    assert a.loc[1, "primary_count"] == 14

def test_neuropil_subgraph_mask_min_size():
    nodes = np.array([1, 2, 3, 4, 5])
    a = pd.DataFrame({"root_id": [1, 2, 3, 4], "primary_neuropil": ["A", "A", "B", "B"]})
    masks = stage_b.neuropil_subgraph_mask(nodes, a)
    assert masks == {}  # all below MIN_NEUROPIL_NEURONS
    stage_b.MIN_NEUROPIL_NEURONS = 2
    masks = stage_b.neuropil_subgraph_mask(nodes, a)
    assert set(masks) == {"A", "B"} and masks["A"].sum() == 2 and masks["B"].sum() == 2
    stage_b.MIN_NEUROPIL_NEURONS = 200

def test_permutation_test_detects_structure():
    rng = np.random.default_rng(0)
    gs = {}
    labels = {}
    for k in range(12):
        cls = "X" if k < 6 else "Y"
        center = 0.0 if cls == "X" else 10.0
        gs[f"np{k}"] = center + rng.normal(0, 0.1, 5)
        labels[f"np{k}"] = cls
    obs, p = stage_b.permutation_test_class_difference(gs, labels, n_perm=500, seed=1)
    assert p < 0.05
    # unstructured labels -> not significant
    rng2 = np.random.default_rng(2)
    labels2 = {k: v for k, v in zip(gs, rng2.permutation(["X"]*6 + ["Y"]*6))}
    # rebuild identical points without class structure
    gs2 = {f"np{k}": rng.normal(0, 1, 5) for k in range(12)}
    labels2 = {f"np{k}": ("X" if k < 6 else "Y") for k in range(12)}
    obs2, p2 = stage_b.permutation_test_class_difference(gs2, labels2, n_perm=500, seed=3)
    assert p2 > 0.05

def test_stage_b_null_path_seeded_and_valid():
    """Stage B runner must use seeded numpy nulls (AMENDMENT-3): same seed -> identical
    rewired graph; degree sequence and edge count preserved; no self-loops/multi-edges."""
    import nulls, scipy.sparse as sp
    rng = np.random.default_rng(7)
    n, m = 300, 2000
    pre = rng.integers(0, n, m); post = rng.integers(0, n, m)
    A = sp.csr_matrix((np.ones(m), (pre, post)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    s, d = A.nonzero()
    p1, q1 = nulls.dp_rewire_np(s, d, n, 10 * A.nnz, seed=42)
    p2, q2 = nulls.dp_rewire_np(s, d, n, 10 * A.nnz, seed=42)
    assert np.array_equal(p1, p2) and np.array_equal(q1, q2)  # deterministic
    B = sp.csr_matrix((np.ones(len(p1)), (p1, q1)), shape=(n, n))
    assert B.nnz == A.nnz                                     # edge count preserved
    assert np.array_equal(np.diff(B.indptr), np.diff(A.indptr)) or \
           np.array_equal(np.sort(np.diff(B.indptr)), np.sort(np.diff(A.indptr)))  # out-deg seq
    in_a = np.bincount(d, minlength=n); in_b = np.bincount(q1, minlength=n)
    assert np.array_equal(in_a, in_b)                         # in-degree preserved exactly
    p3, q3 = nulls.dp_rewire_np(s, d, n, 10 * A.nnz, seed=43)
    assert not (np.array_equal(p1, p3) and np.array_equal(q1, q3))  # different seed differs
