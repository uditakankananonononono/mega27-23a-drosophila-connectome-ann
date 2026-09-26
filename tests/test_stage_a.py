import itertools
import numpy as np
import networkx as nx
import igraph as ig
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
import stage_a, graph_io

TRIAD_LABELS = stage_a.TRIAD_LABELS


def brute_triad_census(n, edges):
    """Reference: enumerate every 3-node subset, classify with networkx."""
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    G.add_edges_from(edges)
    counts = {k: 0 for k in TRIAD_LABELS}
    for tri in itertools.combinations(range(n), 3):
        t = nx.triad_type(G.subgraph(tri))
        counts[t] += 1
    return counts


def rng_graph(n=25, m=80, seed=1):
    rng = np.random.default_rng(seed)
    edges = set()
    while len(edges) < m:
        a, b = rng.integers(0, n, 2)
        if a != b:
            edges.add((int(a), int(b)))
    return n, sorted(edges)


def test_triad_census_matches_bruteforce():
    n, edges = rng_graph()
    g = ig.Graph(n=n, edges=edges, directed=True)
    got = stage_a.triad_census(g)
    ref = brute_triad_census(n, edges)
    assert got == ref, f"mismatch: { {k: (got[k], ref[k]) for k in got if got[k] != ref[k]} }"


def test_degree_preserving_null_keeps_degrees():
    n, edges = rng_graph(n=30, m=120, seed=2)
    g = ig.Graph(n=n, edges=edges, directed=True)
    h = stage_a.degree_preserving_null(g, n_swaps_per_edge=5, seed=3)
    assert sorted(g.degree(mode="in")) == sorted(h.degree(mode="in"))
    assert sorted(g.degree(mode="out")) == sorted(h.degree(mode="out"))
    assert g.ecount() == h.ecount()
    assert set(g.get_edgelist()) != set(h.get_edgelist())  # actually rewired


def test_er_null_dimensions():
    h = stage_a.er_null(50, 200, seed=4)
    assert h.vcount() == 50 and h.ecount() == 200 and h.is_directed()
    assert not any(h.is_loop())


def test_motif_zscores():
    obs = {"030T": 100.0, "300": 5.0}
    nulls = [{"030T": 40.0, "300": 20.0}, {"030T": 60.0, "300": 40.0}, {"030T": 50.0, "300": 30.0}]
    z, mu, sd = stage_a.motif_zscores(obs, nulls)
    assert abs(mu["030T"] - 50.0) < 1e-9 and abs(mu["300"] - 30.0) < 1e-9
    assert z["030T"] > 0 and z["300"] < 0


def test_bh_fdr_monotone():
    p = [0.001, 0.01, 0.04, 0.5]
    q = stage_a.bh_fdr(p)
    assert list(q) == sorted(q) or all(q[i] <= q[i+1] + 1e-9 for i in range(len(q)-1))
    assert q[0] <= q[-1] and all(0 <= x <= 1 for x in q)
    assert abs(q[0] - 0.004) < 1e-9  # 0.001 * 4/1


def test_aggregate_and_threshold():
    df = pd.DataFrame({
        "pre_pt_root_id": [1, 1, 1, 2, 3],
        "post_pt_root_id": [2, 2, 3, 3, 1],
        "neuropil": ["A", "B", "A", "A", "A"],
        "syn_count": [3, 4, 1, 6, 10],
    })
    agg = graph_io.aggregate_edges(df)
    row12 = agg[(agg.pre_pt_root_id == 1) & (agg.post_pt_root_id == 2)]
    assert row12["syn_count"].iloc[0] == 7  # summed over neuropils
    thr = graph_io.threshold_edges(agg, 5)
    pairs = set(zip(thr.pre_pt_root_id, thr.post_pt_root_id))
    assert pairs == {(1, 2), (2, 3), (3, 1)}  # (1,3) with 1 synapse dropped


def test_build_arrays_roundtrip():
    df = pd.DataFrame({"pre_pt_root_id": [10, 10, 20], "post_pt_root_id": [20, 30, 30], "syn_count": [5, 6, 7]})
    nodes, src, dst, w = graph_io.build_arrays(df)
    g = graph_io.to_igraph(nodes, src, dst, w)
    assert g.vcount() == 3 and g.ecount() == 3
    rid = g.vs["root_id"]
    el = {(rid[a], rid[b]) for a, b in g.get_edgelist()}
    assert el == {(10, 20), (10, 30), (20, 30)}
    assert sorted(g.es["weight"]) == [5.0, 6.0, 7.0]


def test_rich_club():
    # star: center connected to all, spokes not interconnected
    n = 11
    edges = [(0, i) for i in range(1, n)] + [(i, 0) for i in range(1, n)]
    g = ig.Graph(n=n, edges=edges, directed=True)
    rc = stage_a.rich_club_coefficient(g, ks=[1, 5])
    # k=1: every node has total degree 2+ (center 20, spokes 2) -> club = all 11 nodes,
    # 20 directed edges among them -> phi = 2*20/(11*10) = 4/11
    assert abs(rc[1] - 4.0/11.0) < 1e-12
    # k=5: only the center qualifies -> undefined (nan)
    assert rc[5] != rc[5]
