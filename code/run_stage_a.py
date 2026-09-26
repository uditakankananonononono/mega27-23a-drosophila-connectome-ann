"""Stage A runner v3 (locked spec; fast exact census; checkpointing).
Census implementation: fast_census (exact rational solve; 166-case exact
validation vs igraph in tests/test_fast_census.py + real-graph cross-check).
igraph used ONLY for null-graph generation (rewire / ER)."""
import json, os, sys, time
import numpy as np
import polars as pl
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import stage_a, fast_census

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
N_NULL = 100
MASTER_SEED = 23
CKPT = os.path.join(OUT, "stage_a_results.json")

def save(res):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f)
    os.replace(tmp, CKPT)

def csr_from_igraph(g):
    return fast_census._to_csr(g)

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    edges = pl.read_parquet(os.path.join(OUT, "edges_ge5.parquet"))
    nodes = pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy()
    index = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((index[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((index[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    n = len(nodes)
    A = sp.csr_matrix((np.ones(edges.height, dtype=np.int64), (src, dst)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    import igraph as ig
    g = ig.Graph(n=n, edges=list(zip(src.tolist(), dst.tolist())), directed=True)
    g.vs["root_id"] = nodes.tolist()
    print(f"graph: {n:,} nodes, {g.ecount():,} edges [{time.time()-t0:.0f}s]", flush=True)

    res = dict(params=dict(threshold=5, n_null=N_NULL, master_seed=MASTER_SEED,
                           n_nodes=n, n_edges=g.ecount(),
                           census_impl="fast_census exact-rational (validated vs igraph: 166 synthetic cases + real-graph cross-check)"))
    tc = time.time()
    res["observed"] = fast_census.census(A)
    res["params"]["census_seconds_observed"] = time.time() - tc
    res["reciprocity"] = stage_a.reciprocity_binary(g)
    deg = g.degree(mode="all")
    ks = sorted(set(int(x) for x in np.percentile(deg, [50, 75, 90, 95, 99])))
    res["rich_club"] = {str(k): v for k, v in stage_a.rich_club_coefficient(g, ks).items()}
    res["degree_percentile_ks"] = ks
    gu = ig.Graph(n=n, edges=g.get_edgelist(), directed=False)
    gu.simplify()
    comm = gu.community_multilevel(return_levels=False)
    res["modularity"] = comm.modularity  # Louvain on symmetrized graph (locked: modularity, resolution 1.0)
    res["n_communities"] = len(set(comm.membership))
    del gu
    save(res)
    print(f"observed stats saved (census {res['params']['census_seconds_observed']:.0f}s) [{time.time()-t0:.0f}s]", flush=True)
    del A

    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(2 * N_NULL)]

    null2 = []
    for i in range(N_NULL):
        h2 = stage_a.er_null(n, g.ecount(), seed=seeds[N_NULL + i])
        null2.append(fast_census.census(csr_from_igraph(h2))); del h2
        if (i + 1) % 10 == 0:
            res["null_er"] = null2; save(res)
            print(f"ER nulls {i+1}/{N_NULL} [{time.time()-t0:.0f}s]", flush=True)
    res["null_er"] = null2; save(res)
    print(f"ER family done [{time.time()-t0:.0f}s]", flush=True)

    null1 = []
    for i in range(N_NULL):
        h1 = stage_a.degree_preserving_null(g, n_swaps_per_edge=10, seed=seeds[i])
        null1.append(fast_census.census(csr_from_igraph(h1))); del h1
        res["null_dp"] = null1; save(res)
        print(f"DP nulls {i+1}/{N_NULL} [{time.time()-t0:.0f}s]", flush=True)
    res["null_dp"] = null1

    z1, mu1, sd1 = stage_a.motif_zscores(res["observed"], null1)
    z2, mu2, sd2 = stage_a.motif_zscores(res["observed"], null2)
    res.update(z_vs_degree_preserving=z1, z_vs_er=z2,
               null1_mean=mu1, null1_sd=sd1, null2_mean=mu2, null2_sd=sd2,
               elapsed_s=time.time() - t0)
    save(res)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
