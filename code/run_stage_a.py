"""Stage A runner v4 (locked spec; AMENDMENT-3 seeded numpy nulls).
Null definitions UNCHANGED from PREREGISTRATION sec 3 (DP: 10 successful
simple swaps/edge; ER: directed G(n,m)). Implementation swapped to code/nulls.py
(numpy, seeded) after v3 was found to IGNORE seeds in both families (igraph
global RNG) and to need ~750s/DP null. v4: full reproducibility + ~83s/DP rewire
(bench: degrees/simple/noloop verified on the real graph).
Census: fast_census exact-rational solve; validated vs igraph on 166 synthetic
cases (tests/test_fast_census.py). Real-graph igraph cross-check: PENDING
(scheduled after Stage A; do not cite as done)."""
import json, os, sys, time, random
import numpy as np
import polars as pl
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import stage_a, fast_census, nulls

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
N_NULL = 100
MASTER_SEED = 23
CKPT = os.path.join(OUT, "stage_a_results.json")

def save(res):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f)
    os.replace(tmp, CKPT)

def csr_from_arrays(pre, post, n):
    A = sp.csr_matrix((np.ones(len(pre), dtype=np.int64), (pre, post)), shape=(n, n))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    return A

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    edges = pl.read_parquet(os.path.join(OUT, "edges_ge5.parquet"))
    nodes = pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy()
    index = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((index[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((index[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    n = len(nodes)
    key = src * n + dst
    _, ui = np.unique(key, return_index=True)
    src, dst = src[ui], dst[ui]
    kp = src != dst
    src, dst = src[kp], dst[kp]
    A = csr_from_arrays(src, dst, n)
    E = A.nnz
    import igraph as ig
    ig.set_random_number_generator(random.Random(MASTER_SEED))
    g = ig.Graph(n=n, edges=list(zip(src.tolist(), dst.tolist())), directed=True)
    g.vs["root_id"] = nodes.tolist()
    print(f"graph: {n:,} nodes, {E:,} edges [{time.time()-t0:.0f}s]", flush=True)

    prev = {}
    if os.path.exists(CKPT):
        try:
            prev = json.load(open(CKPT))
        except Exception:
            prev = {}
    resume_ok = prev.get("params", {}).get("runner") == "v4"
    res = dict(params=dict(threshold=5, n_null=N_NULL, master_seed=MASTER_SEED,
                           n_nodes=n, n_edges=E, runner="v4",
                           nulls_impl="code/nulls.py seeded numpy (AMENDMENT-3)",
                           census_impl="fast_census exact-rational (validated vs igraph: 166 synthetic cases; real-graph cross-check pending)"))
    if resume_ok:
        if prev.get("null_er"): res["null_er"] = prev["null_er"]
        if prev.get("null_dp"): res["null_dp"] = prev["null_dp"]
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
    res["modularity"] = comm.modularity  # Louvain, resolution 1.0, seeded RNG (AMENDMENT-3)
    res["n_communities"] = len(set(comm.membership))
    del gu, g
    save(res)
    print(f"observed stats saved (census {res['params']['census_seconds_observed']:.0f}s) [{time.time()-t0:.0f}s]", flush=True)

    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = [int(s.generate_state(1)[0]) for s in ss.spawn(2 * N_NULL)]

    # resume: reuse only nulls from the same seeded runner version
    null2 = list(prev.get("null_er", [])) if resume_ok else []
    if null2:
        print(f"resuming: {len(null2)} ER nulls from checkpoint", flush=True)
    for i in range(len(null2), N_NULL):
        p2, q2 = nulls.er_null_np(n, E, seed=seeds[N_NULL + i])
        null2.append(fast_census.census(csr_from_arrays(p2, q2, n)))
        if (i + 1) % 10 == 0:
            res["null_er"] = null2; save(res)
            print(f"ER nulls {i+1}/{N_NULL} [{time.time()-t0:.0f}s]", flush=True)
    res["null_er"] = null2; save(res)
    print(f"ER family done [{time.time()-t0:.0f}s]", flush=True)

    null1 = list(prev.get("null_dp", [])) if resume_ok else []
    if null1:
        print(f"resuming: {len(null1)} DP nulls from checkpoint", flush=True)
    for i in range(len(null1), N_NULL):
        p1, q1 = nulls.dp_rewire_np(src, dst, n, 10 * E, seed=seeds[i])
        null1.append(fast_census.census(csr_from_arrays(p1, q1, n)))
        res["null_dp"] = null1; save(res)
        print(f"DP nulls {i+1}/{N_NULL} [{time.time()-t0:.0f}s]", flush=True)
    res["null_dp"] = null1

    from scipy.stats import norm
    z1, mu1, sd1 = stage_a.motif_zscores(res["observed"], null1)
    z2, mu2, sd2 = stage_a.motif_zscores(res["observed"], null2)
    labels = list(res["observed"].keys())
    p1 = [float(2 * norm.sf(abs(z1[k]))) for k in labels]
    p2 = [float(2 * norm.sf(abs(z2[k]))) for k in labels]
    q1 = stage_a.bh_fdr(p1); q2 = stage_a.bh_fdr(p2)
    res.update(z_vs_degree_preserving=z1, z_vs_er=z2,
               null1_mean=mu1, null1_sd=sd1, null2_mean=mu2, null2_sd=sd2,
               p_vs_degree_preserving=dict(zip(labels, p1)), p_vs_er=dict(zip(labels, p2)),
               q_vs_degree_preserving=dict(zip(labels, map(float, q1))),
               q_vs_er=dict(zip(labels, map(float, q2))),
               elapsed_s=time.time() - t0)
    save(res)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
