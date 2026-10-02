"""Robustness sweep over edge threshold T in {10, 50} (subsets of the locked >=5 graph; T=1 needs the raw table and is not run here).
Observed triad census + N1 (degree-preserving, 10 swaps/edge) nulls, 10 per threshold; z = (obs-mu)/sd (F1). Descriptive sensitivity, not a moved gate."""
import sys, json, time, numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, "code"); import fast_census, nulls
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
out = {}
NN = 10
for T in (10, 50):
    s = d[d.syn_count >= T]
    ids, inv = np.unique(np.concatenate([s.pre_pt_root_id.values, s.post_pt_root_id.values]), return_inverse=True)
    n = len(ids); pre = inv[:len(s)].astype(np.int64); post = inv[len(s):].astype(np.int64)
    def census(p, q):
        A = sp.csr_matrix((np.ones(len(p), dtype=np.int64), (p, q)), shape=(n, n)); A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
        return fast_census.census(A)
    obs = census(pre, post); nl = []
    t0 = time.time()
    for k in range(NN):
        p2, q2 = nulls.dp_rewire_fast(pre.copy(), post.copy(), n, 10 * len(pre), 5000 + k); nl.append(census(p2, q2))
        print(T, k, round(time.time() - t0), flush=True)
    res = {}
    for c in obs:
        v = np.array([x[c] for x in nl], dtype=float); sd = v.std(ddof=1)
        res[c] = {"obs": float(obs[c]), "mu": float(v.mean()), "sd": float(sd), "z": float((obs[c] - v.mean()) / sd) if sd > 0 else None}
    out[str(T)] = {"n_nodes": n, "n_edges": int(len(pre)), "n_null": NN, "classes": res}
    json.dump(out, open("results/stage_a/threshold_sweep.json", "w"), indent=1)
for T, v in out.items(): print(T, v["n_nodes"], v["n_edges"], {c: (round(r["z"]) if r["z"] else None) for c, r in v["classes"].items()})
