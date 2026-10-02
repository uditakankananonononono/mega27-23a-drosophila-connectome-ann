"""Prereg A3 (DP family): add independent degree-preserving nulls (new seeds, C engine, 10 swaps/edge) to the locked 100 and check z stability of the headline classes. Checkpoints after each null."""
import sys, json, time, os, ctypes, numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, "code"); import fast_census
_L = ctypes.CDLL('code/dp_rewire_c.so'); _L.dp_rewire_c.restype = ctypes.c_longlong; _L.dp_rewire_c.argtypes = [ctypes.c_void_p]*2 + [ctypes.c_longlong]*3 + [ctypes.c_uint64]
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
ids, inv = np.unique(np.concatenate([d.pre_pt_root_id.values, d.post_pt_root_id.values]), return_inverse=True)
n = len(ids); pre = inv[:len(d)].astype(np.int64); post = inv[len(d):].astype(np.int64)
key = np.unique(pre * n + post); key = key[(key // n) != (key % n)]; pre = key // n; post = key % n; E = len(pre)
OUT = "results/stage_a/dp_sensitivity.json"
try: res = json.load(open(OUT))
except Exception: res = {"n": int(n), "E": int(E), "dp_extra": []}
NT = int(sys.argv[1]); t0 = time.time()
while len(res["dp_extra"]) < NT:
    k = len(res["dp_extra"]); p = pre.copy(); q = post.copy(); acc = _L.dp_rewire_c(p.ctypes.data, q.ctypes.data, E, n, 10 * E, 90000 + k); assert acc == 10 * E
    A = sp.csr_matrix((np.ones(E, dtype=np.int64), (p, q)), shape=(n, n)); A.sum_duplicates(); A.data[:] = 1; A.setdiag(0); A.eliminate_zeros()
    res["dp_extra"].append({c: float(v) for c, v in fast_census.census(A).items()})
    json.dump(res, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT); print(k, round(time.time() - t0), flush=True)
