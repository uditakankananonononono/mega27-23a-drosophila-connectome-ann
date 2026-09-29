"""C rewire engine (code/dp_rewire_c.so): same acceptance semantics as dp_rewire_fast,
validated by invariant tests + statistical cross-check (see commit message)."""
import ctypes, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

LIB = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "..", "code", "dp_rewire_c.so"))
LIB.dp_rewire_c.restype = ctypes.c_longlong
LIB.dp_rewire_c.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_longlong,
                            ctypes.c_longlong, ctypes.c_longlong, ctypes.c_uint64]

def c_rewire(pre, post, n, swaps, seed):
    p = pre.astype(np.int64).copy(); q = post.astype(np.int64).copy()
    acc = LIB.dp_rewire_c(p.ctypes.data, q.ctypes.data, len(p), n, swaps, seed)
    return p, q, acc

def _graph(n=3000, e=15000, seed=7):
    rng = np.random.default_rng(seed)
    pre = rng.integers(0, n, e); post = rng.integers(0, n, e)
    m = pre != post
    keys = set(zip(pre[m].tolist(), post[m].tolist()))
    pre = np.array([k[0] for k in keys], dtype=np.int64)
    post = np.array([k[1] for k in keys], dtype=np.int64)
    return pre, post, n

def test_invariants_degrees_simple_loopless():
    pre, post, n = _graph()
    p2, q2, acc = c_rewire(pre, post, n, 10 * len(pre), 42)
    assert acc == 10 * len(pre)
    assert sorted(pre.tolist()) == sorted(p2.tolist())          # in-degree multiset
    assert (np.bincount(post, minlength=n) == np.bincount(q2, minlength=n)).all()  # out-degree
    assert (p2 != q2).all()                                      # no loops
    k2 = p2 * n + q2
    assert len(set(k2.tolist())) == len(k2)                      # no duplicates

def test_deterministic_seeded():
    pre, post, n = _graph()
    a1, b1, _ = c_rewire(pre, post, n, 5 * len(pre), 42)
    a2, b2, _ = c_rewire(pre, post, n, 5 * len(pre), 42)
    a3, b3, _ = c_rewire(pre, post, n, 5 * len(pre), 43)
    assert (a1 == a2).all() and (b1 == b2).all()
    assert not (b1 == b3).all()

def test_hub_graph_no_dups():
    rng = np.random.default_rng(11)
    n = 2000
    hub = np.zeros(5000, dtype=np.int64)                       # heavy out-hub
    post = rng.integers(0, n, 5000)
    pre2 = rng.integers(0, n, 5000); post2 = np.zeros(5000, dtype=np.int64)  # heavy in-hub
    pre = np.concatenate([hub, pre2]); post = np.concatenate([post, post2])
    m = pre != post
    keys = set(zip(pre[m].tolist(), post[m].tolist()))
    pre = np.array([k[0] for k in keys]); post = np.array([k[1] for k in keys])
    p2, q2, acc = c_rewire(pre, post, n, 10 * len(pre), 99)
    k2 = p2 * n + q2
    assert len(set(k2.tolist())) == len(k2)
    assert (p2 != q2).all()
