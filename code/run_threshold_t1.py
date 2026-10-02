"""T=1 threshold (all connected pairs, 15,091,983 edges) triad census + N1 nulls (5, 10 swaps/edge). Needs /tmp/edges_ge1.parquet built by code/build_edges_ge1.py from the raw table."""
import sys, json, time, os, numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, "code"); import fast_census, nulls, ctypes
_L = ctypes.CDLL('code/dp_rewire_c.so'); _L.dp_rewire_c.restype = ctypes.c_longlong; _L.dp_rewire_c.argtypes = [ctypes.c_void_p]*2 + [ctypes.c_longlong]*3 + [ctypes.c_uint64]
def rewire(p, q, n, swaps, seed):
    p = p.astype(np.int64); q = q.astype(np.int64); acc = _L.dp_rewire_c(p.ctypes.data, q.ctypes.data, len(p), n, swaps, seed); assert acc == swaps, acc; return p, q
fast_census._blocked_masked_sums2.__defaults__ = (int(os.environ.get('BLK', '150')),)  # memory-bounded blocks; exact integer result unchanged
roots = np.load("data/raw/proofread_root_ids_783.npy"); n = len(roots)
pre = np.load("/tmp/t1_pre.npy"); post = np.load("/tmp/t1_post.npy")  # int32 indices prepared from /tmp/edges_ge1.parquet (searchsorted into sorted root ids)
OUT = "results/stage_a/threshold_t1.json"
def census(p, q):
    A = sp.csr_matrix((np.ones(len(p), dtype=np.int8), (p, q)), shape=(n, n)); A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros(); A = A.astype(np.int32)  # int8 build for memory; int32 holds wedge counts (<=139k) exactly
    return {c: float(v) for c, v in fast_census.census(A).items()}
try: res = json.load(open(OUT))
except Exception: res = {"n_nodes": int(n), "n_edges": int(len(pre)), "observed": None, "nulls": []}
t0 = time.time()
if res["observed"] is None:
    res["observed"] = census(pre.astype(np.int64), post.astype(np.int64)); json.dump(res, open(OUT, "w")); print("observed", round(time.time() - t0), flush=True)
NN = int(sys.argv[1])
while len(res["nulls"]) < NN:
    k = len(res["nulls"]); p2, q2 = rewire(pre, post, n, 10 * len(pre), 8000 + k)
    res["nulls"].append(census(p2, q2)); del p2, q2; import gc; gc.collect(); json.dump(res, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT); print("null", k, round(time.time() - t0), flush=True)
