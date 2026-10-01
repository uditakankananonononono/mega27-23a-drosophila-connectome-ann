"""F-rich-club: phi(k)=2E_{>k}/(N_{>k}(N_{>k}-1)) on the undirected simple projection (total degree), normalised by degree-preserving rewired nulls (nulls.dp_rewire_fast)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "code"); import nulls
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
ids, inv = np.unique(np.concatenate([d.pre_pt_root_id.values, d.post_pt_root_id.values]), return_inverse=True)
n = len(ids); pre = inv[:len(d)].astype(np.int64); post = inv[len(d):].astype(np.int64)
def phi(pre, post, ks):
    a = np.minimum(pre, post); b = np.maximum(pre, post); m = a != b
    key = np.unique(a[m] * n + b[m]); u, v = key // n, key % n
    deg = np.bincount(u, minlength=n) + np.bincount(v, minlength=n)
    out = {}
    for k in ks:
        sel = deg > k; N = int(sel.sum())
        E = int((sel[u] & sel[v]).sum())
        out[k] = (N, E, 2 * E / (N * (N - 1)) if N > 1 else None)
    return out
ks = [10, 25, 50, 100, 200, 300, 400, 500]
obs = phi(pre, post, ks)
res = {"n_nodes": n, "k": ks, "observed": {str(k): obs[k] for k in ks}, "null": {}}
NN = 5
nl = []
for s in range(NN):
    p2, q2 = nulls.dp_rewire_fast(pre.copy(), post.copy(), n, 10 * len(pre), 1000 + s)
    nl.append(phi(p2, q2, ks)); print("null", s, flush=True)
for k in ks:
    v = np.array([x[k][2] for x in nl]); res["null"][str(k)] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "ratio": obs[k][2] / float(v.mean())}
json.dump(res, open("results/stage_a/rich_club.json", "w"), indent=1)
for k in ks: print(k, obs[k], res["null"][str(k)])
