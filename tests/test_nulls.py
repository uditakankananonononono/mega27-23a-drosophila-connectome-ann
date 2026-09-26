import numpy as np, sys
sys.path.insert(0, 'code')
from nulls import er_null_np, dp_rewire_np

def small_graph(seed=0, n=200, m=800):
    return er_null_np(n, m, seed)

def test_er_exact_and_simple():
    pre, post = er_null_np(5000, 20000, 42)
    assert len(pre) == 20000
    assert (pre != post).all()
    assert len(set((pre * 5000 + post).tolist())) == 20000

def test_er_reproducible():
    a = er_null_np(1000, 3000, 7); b = er_null_np(1000, 3000, 7); c = er_null_np(1000, 3000, 8)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    assert not np.array_equal(a[0], c[0])

def test_dp_preserves_degrees_and_simplicity():
    pre, post = small_graph()
    n = 200
    io = lambda p, q: (np.bincount(p, minlength=n), np.bincount(q, minlength=n))
    o0, i0 = io(pre, post)
    p2, q2 = dp_rewire_np(pre, post, n, 10 * len(pre), seed=1)
    o1, i1 = io(p2, q2)
    assert np.array_equal(o0, o1) and np.array_equal(i0, i1)
    assert (p2 != q2).all()
    assert len(set((p2 * n + q2).tolist())) == len(p2)

def test_dp_reproducible_and_changes():
    pre, post = small_graph()
    a = dp_rewire_np(pre, post, 200, 8000, seed=5)
    b = dp_rewire_np(pre, post, 200, 8000, seed=5)
    c = dp_rewire_np(pre, post, 200, 8000, seed=6)
    assert np.array_equal(a[1], b[1]) and not np.array_equal(a[1], c[1])
    assert not np.array_equal(a[1], post)
