"""Stage B runner (locked spec, PREREGISTRATION.md section 4).
Reads: edges_ge5.parquet + verified neuropil tables. Writes results/stage_b/.
Per-neuropil induced subgraphs (>=200 neurons), triad census + dual nulls (25 reps each,
B-family budget), stratified z-scores, class-difference permutation test (10k perms)."""
import json, os, sys, time
import numpy as np
import pandas as pd
import polars as pl
import scipy.sparse as sp
sys.path.insert(0, os.path.dirname(__file__))
import stage_a, stage_b, fast_census

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")
OUT = os.path.join(os.path.dirname(__file__), "..", "results", "stage_b")
N_NULL_B = 25
MASTER_SEED = 24

def save(res):
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "stage_b_results.json.tmp")
    with open(tmp, "w") as f:
        json.dump(res, f)
    os.replace(tmp, os.path.join(OUT, "stage_b_results.json"))

def build_subgraph(src, dst, mask):
    idx = np.full(len(mask), -1, dtype=np.int64)
    idx[mask] = np.arange(mask.sum())
    keep = mask[src] & mask[dst]
    s2, d2 = idx[src[keep]], idx[dst[keep]]
    A = sp.csr_matrix((np.ones(keep.sum(), dtype=np.int64), (s2, d2)),
                      shape=(mask.sum(), mask.sum()))
    A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    edges = list(zip(s2.tolist(), d2.tolist()))
    import igraph as ig
    g = ig.Graph(n=int(mask.sum()), edges=edges, directed=True)
    return A, g

def main():
    t0 = time.time()
    edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
    nodes = pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy()
    index = {r: i for i, r in enumerate(nodes)}
    src = np.fromiter((index[r] for r in edges["pre_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    dst = np.fromiter((index[r] for r in edges["post_pt_root_id"].to_numpy()), dtype=np.int64, count=edges.height)
    assign = stage_b.assign_primary_neuropil(
        os.path.join(RAW, "per_neuron_neuropil_count_pre_783.feather"),
        os.path.join(RAW, "per_neuron_neuropil_count_post_783.feather"))
    assign.to_csv(os.path.join(OUT if os.path.exists(OUT) else ".", "neuropil_assignment.csv"), index=False)
    masks = stage_b.neuropil_subgraph_mask(nodes, assign)
    print(f"assigned {len(assign):,} neurons; {len(masks)} testable neuropils [{time.time()-t0:.0f}s]", flush=True)

    res = {"params": dict(min_neurons=stage_b.MIN_NEUROPIL_NEURONS, n_null=N_NULL_B, master_seed=MASTER_SEED),
           "neuropils": {}}
    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = iter(int(s.generate_state(1)[0]) for s in ss.spawn(4 * len(masks) * N_NULL_B))
    for name, mask in sorted(masks.items()):
        ts = time.time()
        A, g = build_subgraph(src, dst, mask)
        if g.ecount() < 50:
            print(f"skip {name}: {g.ecount()} edges", flush=True)
            continue
        obs = fast_census.census(A)
        null_dp, null_er = [], []
        for i in range(N_NULL_B):
            h1 = stage_a.degree_preserving_null(g, n_swaps_per_edge=10, seed=next(seeds))
            null_dp.append(fast_census.census(fast_census._to_csr(h1))); del h1
            h2 = stage_a.er_null(g.vcount(), g.ecount(), seed=next(seeds))
            null_er.append(fast_census.census(fast_census._to_csr(h2))); del h2
        zdp, _, _ = stage_a.motif_zscores(obs, null_dp)
        zer, _, _ = stage_a.motif_zscores(obs, null_er)
        res["neuropils"][name] = dict(n=int(mask.sum()), m=g.ecount(), observed=obs,
                                      z_dp=zdp, z_er=zer)
        save(res)
        print(f"{name}: n={mask.sum()} m={g.ecount()} [{time.time()-ts:.0f}s]", flush=True)
    res["elapsed_s"] = time.time() - t0
    save(res)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
