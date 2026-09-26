import numpy as np, sys
sys.path.insert(0, 'code')
from n3_null import primary_neuropil, edge_compartments, n3_rewire
from nulls import er_null_np

def test_primary_neuropil():
    d = primary_neuropil([1,1,2], ["A","B","C"], [5,9,3])
    assert d == {1:"B", 2:"C"}

def test_n3_preserves_degrees_and_compartments():
    pre, post = er_null_np(300, 1500, 4)
    comp_pre = np.random.default_rng(0).choice(["X","Y"], 300)
    comp_post = np.random.default_rng(1).choice(["P","Q"], 300)
    ep, eq = comp_pre[pre], comp_post[post]
    p2, q2, stats = n3_rewire(pre, post, ep, eq, 300, 10, seed=7)
    io = lambda a,b,n=300: (np.bincount(a,minlength=n), np.bincount(b,minlength=n))
    assert np.array_equal(io(pre,post)[0], io(p2,q2)[0])
    assert np.array_equal(io(pre,post)[1], io(p2,q2)[1])
    assert np.array_equal(np.sort(comp_pre[p2]), np.sort(comp_pre[pre]))  # multiset of source comps per edge count
    # per-edge compartment pair multiset preserved
    k0 = np.sort(np.char.add(np.char.add(ep.astype(str),"|"), eq.astype(str)))
    k1 = np.sort(np.char.add(np.char.add(comp_pre[p2].astype(str),"|"), comp_post[q2].astype(str)))
    assert np.array_equal(k0, k1)
    assert (p2 != q2).all()
    assert stats["n_groups"] >= 1

def test_n3_reproducible():
    pre, post = er_null_np(200, 800, 5)
    cp = np.random.default_rng(2).choice(["X","Y"], 200)
    cq = np.random.default_rng(3).choice(["P","Q"], 200)
    a = n3_rewire(pre, post, cp[pre], cq[post], 200, 10, seed=9)
    b = n3_rewire(pre, post, cp[pre], cq[post], 200, 10, seed=9)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
