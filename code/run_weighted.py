"""Weighted structure (T=5 graph, weights = summed synapse counts). Three descriptive tests, topology fixed, weights permuted across edges (200 permutations):
 W1 weighted reciprocity r_w = sum_{mutual pairs} 2*min(w_ij,w_ji) / sum_all w  (F11)
 W2 Spearman rho between w_ij and w_ji over mutual pairs (are reciprocal weights coordinated?)
 W3 median weight of edges in mutual pairs vs edges not in mutual pairs."""
import json, numpy as np, pandas as pd
from scipy.stats import spearmanr, rankdata
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
ids, inv = np.unique(np.concatenate([d.pre_pt_root_id.values, d.post_pt_root_id.values]), return_inverse=True)
n = len(ids); p = inv[:len(d)].astype(np.int64); q = inv[len(d):].astype(np.int64); w = d.syn_count.values.astype(np.float64)
k = p != q; p, q, w = p[k], q[k], w[k]
key = p * n + q; o = np.argsort(key); key, p, q, w = key[o], p[o], q[o], w[o]
rkey = q * n + p; pos = np.searchsorted(key, rkey); pos[pos >= len(key)] = 0
mut = key[pos] == rkey; rev = np.where(mut, pos, -1)
a_idx = np.flatnonzero(mut & (p < q)); b_idx = rev[a_idx]
def stats(w):
    rw = 2 * np.minimum(w[a_idx], w[b_idx]).sum() / w.sum()
    rho = spearmanr(w[a_idx], w[b_idx]).statistic
    return rw, rho, np.median(w[mut]), np.median(w[~mut])
obs = stats(w); rng = np.random.default_rng(23); NP = 200; nl = np.array([stats(rng.permutation(w)) for _ in range(NP)])
res = {"n_edges": int(len(w)), "n_mutual_pairs": int(len(a_idx)), "n_perm": NP, "labels": ["weighted_reciprocity", "spearman_mutual_pair_weights", "median_w_mutual_edges", "median_w_nonmutual_edges"],
       "observed": [float(x) for x in obs], "perm_mean": nl.mean(0).tolist(), "perm_sd": nl.std(0, ddof=1).tolist(), "z": [float((obs[i] - nl[:, i].mean()) / nl[:, i].std(ddof=1)) if nl[:, i].std() > 0 else None for i in range(4)],
       "binary_reciprocity": float(mut.sum() / len(w))}
json.dump(res, open("results/stage_a/weighted_structure.json", "w"), indent=1); print(json.dumps(res, indent=1))
