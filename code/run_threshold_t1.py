"""T=1 threshold (all connected pairs, 15,091,983 edges) triad census + N1 nulls (5, 10 swaps/edge). Needs /tmp/edges_ge1.parquet built by code/build_edges_ge1.py from the raw table."""
import sys, json, time, os, numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, "code"); import fast_census, nulls
fast_census._blocked_masked_sums2.__defaults__ = (int(os.environ.get('BLK', '150')),)  # memory-bounded blocks; exact integer result unchanged
import pyarrow.parquet as pq
roots = np.sort(np.load("data/raw/proofread_root_ids_783.npy").astype(np.int64)); n = len(roots)
t = pq.read_table("/tmp/edges_ge1.parquet", columns=["pre_pt_root_id", "post_pt_root_id"])
pre = np.searchsorted(roots, t.column(0).to_numpy()).astype(np.int64); post = np.searchsorted(roots, t.column(1).to_numpy()).astype(np.int64); del t
assert (roots[pre] != 0).all()
OUT = "results/stage_a/threshold_t1.json"
def census(p, q):
    A = sp.csr_matrix((np.ones(len(p), dtype=np.int8), (p, q)), shape=(n, n)); A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    return {c: float(v) for c, v in fast_census.census(A).items()}
try: res = json.load(open(OUT))
except Exception: res = {"n_nodes": int(n), "n_edges": int(len(pre)), "observed": None, "nulls": []}
t0 = time.time()
if res["observed"] is None:
    res["observed"] = census(pre, post); json.dump(res, open(OUT, "w")); print("observed", round(time.time() - t0), flush=True)
NN = int(sys.argv[1])
while len(res["nulls"]) < NN:
    k = len(res["nulls"]); p2, q2 = nulls.dp_rewire_fast(pre.copy(), post.copy(), n, 10 * len(pre), 8000 + k)
    res["nulls"].append(census(p2, q2)); json.dump(res, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT); print("null", k, round(time.time() - t0), flush=True)
