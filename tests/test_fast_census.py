import numpy as np
import igraph as ig
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from fast_census import census_igraph, TRIAD_LABELS


def check(g, tag):
    ref = dict(zip(TRIAD_LABELS, g.triad_census()))
    got = census_igraph(g)
    assert got == ref, f"MISMATCH {tag}: { {k: (got[k], ref[k]) for k in got if got[k] != ref[k]} }"


def test_random_digraphs_exact():
    rng = np.random.default_rng(7)
    for trial in range(40):
        n = int(rng.integers(3, 16)); p = rng.uniform(0.05, 0.95)
        edges = [(i, j) for i in range(n) for j in range(n) if i != j and rng.random() < p]
        check(ig.Graph(n=n, edges=edges, directed=True), f"rand{n}")


def test_structured_exact():
    for n in (10, 30):
        cases = [
            [(0, i) for i in range(1, n)],
            [(i, 0) for i in range(1, n)],
            [(i, (i + 1) % n) for i in range(n)],
            [(i, j) for i in range(n) for j in range(n) if i != j],
            [(2 * i, 2 * i + 1) for i in range(n // 2)] + [(2 * i + 1, 2 * i) for i in range(n // 2)],
        ]
        for e in cases:
            check(ig.Graph(n=n, edges=e, directed=True), "struct")


def test_empty_and_single():
    check(ig.Graph(n=5, edges=[], directed=True), "empty")
    check(ig.Graph(n=3, edges=[(0, 1)], directed=True), "one-edge")


def test_hub_graph_exact():
    rng = np.random.default_rng(11)
    n = 1500
    edges = set()
    for i in range(1, n):
        edges.add((i, int(rng.integers(0, 20))))
        if rng.random() < 0.3:
            edges.add((int(rng.integers(0, n)), i))
    edges = [(a, b) for a, b in edges if a != b]
    check(ig.Graph(n=n, edges=sorted(edges), directed=True), "hub1500")


def test_total_matches_binomial():
    rng = np.random.default_rng(3)
    n = 40
    edges = [(i, j) for i in range(n) for j in range(n) if i != j and rng.random() < 0.3]
    got = census_igraph(ig.Graph(n=n, edges=edges, directed=True))
    assert sum(got.values()) == n * (n - 1) * (n - 2) // 6


def test_dp_rewire_fast_invariants_and_determinism():
    import numpy as np
    import nulls
    n, m = 300, 1200
    pre, post = nulls.er_null_np(n, m, seed=42)
    p, q = nulls.dp_rewire_fast(pre, post, n, 10 * m, seed=7)
    assert (np.bincount(pre, minlength=n) == np.bincount(p, minlength=n)).all()
    assert (np.bincount(post, minlength=n) == np.bincount(q, minlength=n)).all()
    keys = p * n + q
    assert len(set(keys.tolist())) == m
    assert (p != q).all()
    p2, q2 = nulls.dp_rewire_fast(pre, post, n, 10 * m, seed=7)
    assert (p == p2).all() and (q == q2).all()
