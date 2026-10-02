"""Rich-club repeat: hubs by total-degree percentile (50,75,90,95,99,99.5) and the earlier k grid, 20 degree-preserving nulls (C engine, new seeds). phi on the undirected simple projection."""
import sys, json, time, ctypes, numpy as np, pandas as pd
_L = ctypes.CDLL('code/dp_rewire_c.so'); _L.dp_rewire_c.restype = ctypes.c_longlong; _L.dp_rewire_c.argtypes = [ctypes.c_void_p]*2 + [ctypes.c_longlong]*3 + [ctypes.c_uint64]
d = pd.read_parquet("results/stage_a/edges_ge5.parquet")
ids, inv = np.unique(np.concatenate([d.pre_pt_root_id.values, d.post_pt_root_id.values]), return_inverse=True)
n = len(ids); pre = inv[:len(d)].astype(np.int64); post = inv[len(d):].astype(np.int64); E = len(pre)
def phi_at(p, q, thr_fn):
    a = np.minimum(p, q); b = np.maximum(p, q); m = a != b
    key = np.unique(a[m] * n + b[m]); u, v = key // n, key % n
    deg = np.bincount(u, minlength=n) + np.bincount(v, minlength=n)
    out = {}
    for name, k in thr_fn(deg).items():
        sel = deg > k; N = int(sel.sum()); Ee = int((sel[u] & sel[v]).sum()); out[name] = (k, N, Ee, 2 * Ee / (N * (N - 1)) if N > 1 else None)
    return out, deg
PCT = [50, 75, 90, 95, 99, 99.5]; KS = [10, 25, 50, 100, 200, 300, 400, 500]
def thr(deg):
    t = {f"p{x}": float(np.percentile(deg, x)) for x in PCT}; t.update({f"k{k}": k for k in KS}); return t
obs, deg0 = phi_at(pre, post, thr)
# null hubs defined by the OBSERVED thresholds (same k), rather than null percentiles, so that the comparison is at equal degree cutoffs
fixed = {nm: v[0] for nm, v in obs.items()}
NL = []; t0 = time.time()
for s in range(20):
    p = pre.copy(); q = post.copy(); assert _L.dp_rewire_c(p.ctypes.data, q.ctypes.data, E, n, 10 * E, 4000 + s) == 10 * E
    r, _ = phi_at(p, q, lambda deg: fixed); NL.append(r); print(s, round(time.time() - t0), flush=True)
res = {"n_null": 20, "rows": {}}
for nm in obs:
    v = np.array([x[nm][3] for x in NL]); res["rows"][nm] = {"k": obs[nm][0], "N_hubs": obs[nm][1], "E_hubs": obs[nm][2], "phi_obs": obs[nm][3], "phi_null_mean": float(v.mean()), "phi_null_sd": float(v.std(ddof=1)), "ratio": obs[nm][3] / float(v.mean())}
json.dump(res, open("results/stage_a/rich_club_20.json", "w"), indent=1)
for nm, r in res["rows"].items(): print(nm, r)
