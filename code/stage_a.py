"""Stage A analyses (PREREGISTRATION.md section 3). Pure functions; no file I/O."""
import numpy as np
import igraph as ig

TRIAD_LABELS = ["003","012","102","021D","021U","021C","111D","111U","030T","030C","201","120D","120U","120C","210","300"]


def triad_census(g):
    """13-class directed triad census (igraph order matches MAN labels)."""
    counts = g.triad_census()
    assert len(counts) == 16
    return dict(zip(TRIAD_LABELS, counts))


def reciprocity_binary(g):
    return g.reciprocity(mode="default")


def rich_club_coefficient(g, ks):
    deg = np.array(g.degree(mode="all"))
    out = {}
    for k in ks:
        club = [v.index for v in g.vs if deg[v.index] > k]
        nk = len(club)
        if nk < 2:
            out[k] = np.nan
            continue
        ek = g.subgraph(club).ecount()
        out[k] = 2.0 * ek / (nk * (nk - 1))
    return out


def degree_preserving_null(g, n_swaps_per_edge=10, seed=None):
    """Degree-preserving directed rewiring (N1)."""
    rng = np.random.default_rng(seed)
    h = g.copy()
    h.rewire(n=int(n_swaps_per_edge * h.ecount()), allowed_edge_types="simple")
    return h


def er_null(n, m, seed=None):
    rng = int(seed) if seed is not None else None
    return ig.Graph.Erdos_Renyi(n=n, m=m, directed=True, loops=False)


def motif_zscores(obs, null_counts_list):
    """F1: z = (obs - mean_null) / sd_null (sd floored at 1e-9)."""
    M = np.array([[c[k] for k in obs] for c in null_counts_list], dtype=float)
    mu, sd = M.mean(axis=0), M.std(axis=0, ddof=1)
    sd = np.maximum(sd, 1e-9)
    keys = list(obs.keys())
    o = np.array([obs[k] for k in keys], dtype=float)
    return dict(zip(keys, (o - mu) / sd)), dict(zip(keys, mu)), dict(zip(keys, sd))


def bh_fdr(pvals):
    """Benjamini-Hochberg adjusted q-values."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        idx = order[i]
        prev = min(prev, p[idx] * n / (i + 1))
        q[idx] = prev
    return np.minimum(q, 1.0)
