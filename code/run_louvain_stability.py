"""A7/A10: Louvain partition stability across 25 seeded restarts (whole-brain graph).
python-igraph community_multilevel exposes no seed; restarts are realized as seeded
vertex-order permutations (permute_vertices), the standard reproducible-restart
pattern for igraph Louvain. Pairwise variation of information across all restarts,
plus VI to the best-modularity partition. Writes results/stage_a/louvain_stability.json."""
import json, os, sys, time
import numpy as np
import polars as pl
import igraph as ig

OUTA = os.path.join(os.path.dirname(__file__), "..", "results", "stage_a")

def main():
    t0 = time.time()
    edges = pl.read_parquet(os.path.join(OUTA, "edges_ge5.parquet"))
    nodes = np.unique(pl.concat([edges["pre_pt_root_id"], edges["post_pt_root_id"]]).unique().to_numpy())
    idx = {r: i for i, r in enumerate(nodes)}
    src = [idx[r] for r in edges["pre_pt_root_id"].to_numpy()]
    dst = [idx[r] for r in edges["post_pt_root_id"].to_numpy()]
    g = ig.Graph(n=len(nodes), edges=list(zip(src, dst)), directed=True)
    g.es["weight"] = edges["syn_count"].to_numpy() if "syn_count" in edges.columns else [5]*edges.height
    del edges, src, dst
    print(f"graph {g.vcount()} nodes {g.ecount()} edges [{time.time()-t0:.0f}s]", flush=True)
    mods, ncomms, memberships = [], [], []
    N = 25
    for r in range(N):
        tr = time.time()
        rng = np.random.default_rng(23 + r)
        if r == 0:
            h = g  # restart 0 = canonical order (comparable to Stage A single run)
        else:
            perm = rng.permutation(g.vcount()).tolist()
            h = g.permute_vertices(perm)
        c = h.community_multilevel(weights="weight", return_levels=False)
        m = h.modularity(c, weights="weight")
        memb = np.empty(g.vcount(), dtype=np.int64)
        if r == 0:
            memb = np.array(c.membership, dtype=np.int64)
        else:
            inv = np.argsort(perm)  # h vertex j = g vertex perm[j]
            gm = np.array(c.membership, dtype=np.int64)
            memb[perm] = gm  # map back to g vertex order
        mods.append(m); ncomms.append(len(set(memb.tolist()))); memberships.append(memb)
        print(f"restart {r}: modularity={m:.4f} comms={ncomms[-1]} [{time.time()-tr:.0f}s]", flush=True)
    best = int(np.argmax(mods))
    vi_pairs, vi_to_best = [], []
    for i in range(N):
        vi_to_best.append(float(ig.compare_communities(memberships[best].tolist(), memberships[i].tolist(), method="vi")))
        for j in range(i+1, N):
            vi_pairs.append(float(ig.compare_communities(memberships[i].tolist(), memberships[j].tolist(), method="vi")))
    res = {"spec": "A7/A10: 25 seeded vertex-order restarts, igraph community_multilevel, weighted, directed",
           "master_seed": 23, "n_restarts": N,
           "modularity": {"min": min(mods), "max": max(mods), "mean": float(np.mean(mods)), "all": mods},
           "n_communities": {"min": min(ncomms), "max": max(ncomms), "all": ncomms},
           "best_restart": best, "best_modularity": mods[best],
           "vi_pairwise": {"mean": float(np.mean(vi_pairs)), "max": max(vi_pairs), "min": min(vi_pairs)},
           "vi_to_best": {"mean": float(np.mean(vi_to_best)), "max": max(vi_to_best)},
           "note": "VI in [0, log2(n) ~ 17]; near-0 = stable partition. Memberships not stored (large); re-derivable from seeds.",
           "elapsed_s": time.time()-t0}
    json.dump(res, open(os.path.join(OUTA, "louvain_stability.json"), "w"), indent=1)
    print(f"DONE [{time.time()-t0:.0f}s]", flush=True)

if __name__ == "__main__":
    main()
