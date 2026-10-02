"""Prereg A3: null-count sensitivity. Adds NEXT ER nulls (new seeds) to the locked 100 and checks z stability for the headline classes. Checkpoints after each null."""
import sys, json, time, numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, "code"); import fast_census, nulls
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
ids, inv = np.unique(np.concatenate([d.pre_pt_root_id.values, d.post_pt_root_id.values]), return_inverse=True)
n = len(ids); pre = inv[:len(d)].astype(np.int64); post = inv[len(d):].astype(np.int64)
key = np.unique(pre * n + post); key = key[(key // n) != (key % n)]; E = len(key)
OUT = "results/stage_a/null_sensitivity.json"
try: res = json.load(open(OUT))
except Exception: res = {"E": int(E), "n": int(n), "er_extra": []}
N_TARGET = int(sys.argv[1]); t0 = time.time()
while len(res["er_extra"]) < N_TARGET:
    k = len(res["er_extra"]); p, q = nulls.er_null_np(n, E, 70000 + k)
    A = sp.csr_matrix((np.ones(len(p), dtype=np.int64), (p, q)), shape=(n, n)); A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    res["er_extra"].append({c: float(v) for c, v in fast_census.census(A).items()})
    json.dump(res, open(OUT + ".tmp", "w")); import os; os.replace(OUT + ".tmp", OUT)
    print(k, round(time.time() - t0), flush=True)
